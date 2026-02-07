import os
import time
from dataclasses import dataclass
from typing import Callable
from pydantic import BaseModel, Field
from openai import BadRequestError

import streamlit as st
import streamlit.components.v1 as components
from streamlit.delta_generator import DeltaGenerator

from mr_injector.backend.utils import is_debug, booleanize, is_presentation_mode
from mr_injector.frontend.css import get_module_styling, get_exercise_styling

SELECTED_LEVEL_SESSION_KEY = "selected_level"

@dataclass
class ModuleSession:
    was_solved: bool
    num_exercises: int
    exercise_solved: dict[int, bool]

    def is_solved(self):
        return all(list(self.exercise_solved.values()))


class ExercisePlaceholder(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    header: DeltaGenerator = Field(default_factory=st.empty)
    exercise: DeltaGenerator = Field(default_factory=st.empty)
    success_message: DeltaGenerator = Field(default_factory=st.empty)

    def clean(self):
        self.header.empty()
        self.exercise.empty()
        self.success_message.empty()


class ModulePlaceholder(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    header: DeltaGenerator = Field(default_factory=st.empty)
    progress_bar: DeltaGenerator = Field(default_factory=st.empty)
    info: DeltaGenerator = Field(default_factory=st.empty)
    data_selection: DeltaGenerator = Field(default_factory=st.empty)
    levels: DeltaGenerator = Field(default_factory=st.empty)
    exercise_placeholders: list[ExercisePlaceholder]

    def clean_exercises(self):
        for exercise_placeholder in self.exercise_placeholders:
            exercise_placeholder.clean()


def display_task_text_field(task_text: str) -> None:
    st.html(f"""
            <style>
                {get_exercise_styling()}
            </style>
            <div>
                <div class="task-text"><b>Task:</b> {task_text}</div>
            </div>
        """)


def _display_module_header(module_nr: int, title: str, is_solved: bool = False, number_prefix: str = "Module "):
    if is_solved:
        checkmark = '<span class="module-status solved">&#10003;</span> <!-- Checkmark -->'
    else:
        checkmark = '<span class="module-status not-solved">&#10005;</span> <!-- "x" symbol -->'

    st.html(f"""
            <style>
                {get_module_styling()}
            </style>
            <div>
                <div class="module-header">
                    <span class="module-number">{number_prefix}{module_nr}</span>
                    <span class="module-title">{title}</span>
                    {checkmark}
                </div>
            </div>
        """)

def _display_start_next_level_loading_bar():
    placeholder = st.empty()
    time.sleep(1)
    placeholder.progress(0, "Start next level...")
    time.sleep(0.33)
    placeholder.progress(50, "Start next level...")
    time.sleep(0.33)
    placeholder.progress(100, "Start next level...")
    time.sleep(0.33)


class ModuleView:
    """View class to render a exercise module"""

    def __init__(self,
                 title: str,
                 module_nr: int | float,
                 session_key: str,
                 exercises: list[Callable[[], bool | None]],
                 data_selection_fn: Callable[[], None] | None = None,
                 render_exercises_with_level_selectbox: bool = False,
                 jump_to_next_level: bool = False,
                 show_solved_message_by_session: bool = False,
                 description: str = "",
                 layout: str = "centered"):
        self.title = title
        self.description = description
        self.module_nr = module_nr
        self.session_key = session_key
        self.exercises = exercises
        self.render_exercises_with_level_selectbox = render_exercises_with_level_selectbox
        self.jump_to_next_level = jump_to_next_level
        self.show_solved_message_by_session = show_solved_message_by_session
        self.data_selection_fn = data_selection_fn
        self.placeholder: ModulePlaceholder | None = None
        self.layout = layout
        self.on_module_solved_fn: Callable[[], None] | None = None

        self.init_session()

    def init_session(self):
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = ModuleSession(
                was_solved=False,
                num_exercises=len(self.exercises),
                exercise_solved={i: False for i in range(len(self.exercises))}
            )

    def init_placeholders(self) -> None:
        module_header = st.empty()
        module_progress_bar = st.empty()
        module_info = st.empty()
        module_data_selection = st.empty()
        module_levels = st.empty()
        exercise_placeholders = []
        for _ in self.exercises:
            exercise_placeholders.append(
                ExercisePlaceholder()
            )
        self.placeholder = ModulePlaceholder(
            header=module_header,
            progress_bar=module_progress_bar,
            data_selection=module_data_selection,
            info=module_info,
            levels=module_levels,
            exercise_placeholders=exercise_placeholders
        )

    def module_session(self) -> ModuleSession:
        return st.session_state[self.session_key]

    def is_solved(self):
        return self.module_session().is_solved()

    def get_first_not_solved_exercise_index(self) -> int:
        first_not_solved_exercise_index = 0
        for index, solved in self.module_session().exercise_solved.items():
            if not solved:
                first_not_solved_exercise_index = index
                break
        return first_not_solved_exercise_index

    def exercise_placeholder(self, exercise_index: int) -> ExercisePlaceholder:
        assert exercise_index < len(
            self.placeholder.exercise_placeholders), f"Exercise {exercise_index} is not available"
        return self.placeholder.exercise_placeholders[exercise_index]

    def selected_level(self) -> int:
        if len(self.exercises) == 1:
            return 1
        return st.session_state.get(SELECTED_LEVEL_SESSION_KEY, 0)

    def selected_exercise_index(self) -> int:
        return self.selected_level() - 1

    def increment_selected_level(self):
        st.session_state[SELECTED_LEVEL_SESSION_KEY] = self.selected_level() + 1

    def render_level_selectbox(self):
        self.placeholder.levels.empty()
        with self.placeholder.levels:
            levels = [i + 1 for i in range(len(self.exercises))]
            st.selectbox("Level", levels, index=self.get_first_not_solved_exercise_index() if self.jump_to_next_level else 0,
                                      key=SELECTED_LEVEL_SESSION_KEY)

    def render_progress_bar(self):
        percentage_solved = 0
        self.placeholder.progress_bar.progress(percentage_solved, text=f"Exercises solved: ")
        exercised_solved: list[int] = []
        for i, exercise in enumerate(self.exercises):
            if self.module_session().exercise_solved[i]:
                percentage_solved += (1 / len(self.exercises))
                exercised_solved.append(i + 1)
            self.placeholder.progress_bar.progress(percentage_solved, text=f"Exercises solved: {exercised_solved if exercised_solved else ''}")


    def display(self):
        was_solved = False
        self.init_placeholders()

        if len(self.exercises) > 1:
            self.render_progress_bar()
        if self.description and not is_presentation_mode():
            self.placeholder.info.info(self.description)
        if self.render_exercises_with_level_selectbox and len(self.exercises) > 1:
            self.render_level_selectbox()
        if self.data_selection_fn:
            with self.placeholder.data_selection:
                self.data_selection_fn()
        try:
            with self.placeholder.header:
                _display_module_header(self.module_nr, self.title, self.is_solved())
            # with st.expander("Open Exercises", expanded=not self.is_solved()):
            if self.render_exercises_with_level_selectbox:
                with self.exercise_placeholder(self.selected_exercise_index()).exercise.container():
                    if not is_presentation_mode():
                        # Without exercise header we don't need the divider, too
                        st.divider()
                    was_solved = self.render_exercise(self.selected_exercise_index())
            else:
                # render all exercises at once
                for i, exercise in enumerate(self.exercises):
                    self.render_exercise(i)
                    st.divider()

            # auto jump to next level
            # Logic moved to render_exercise to prevent full rerun killing fragment state
            # if self.render_exercises_with_level_selectbox and was_solved and len(self.exercises) > 1:
            #     if self.jump_to_next_level:
            #         _display_start_next_level_loading_bar()
            #         st.rerun()
            #     else:
            #         if self.selected_level() < len(self.exercises):
            #             st.button("Start next level", on_click=self.increment_selected_level)

            # update module header if solved
            if self.is_solved():
                with self.placeholder.header:
                    _display_module_header(self.module_nr, self.title, True)
                if not self.module_session().was_solved:
                    st.balloons()
                    self.module_session().was_solved = True
        except BadRequestError as exp:
            st.error(f"Request Filter. Exception: "
                     f"{exp}")
        except Exception as exp:
            print(exp)
            st.error(f"Error during rendering module: {self.title}")
            if is_debug():
                raise exp

    @st.fragment
    def render_exercise(self, exercise_index: int) -> bool | None:
        """Renders exercise and returns True if it was solved within this function call, or False if not"""
        # If the selected level has changed (e.g. via button callback), trigger full rerun
        # to break out of the fragment and render the new level.
        if self.selected_exercise_index() != exercise_index:
            st.rerun()
            return None

        session_solved = self.module_session().exercise_solved[exercise_index]
        if not is_presentation_mode():
            with self.exercise_placeholder(self.selected_exercise_index()).header:
                _display_module_header(exercise_index + 1, "", session_solved, number_prefix="Exercise ")

        # run exercise
        solved = self.exercises[exercise_index]()

        just_solved = False
        if solved is True and not session_solved:
            self.module_session().exercise_solved[exercise_index] = True
            session_solved = True
            just_solved = True

            # update exercise header immediately if solved
            if not is_presentation_mode():
                with self.exercise_placeholder(self.selected_exercise_index()).header:
                    _display_module_header(exercise_index + 1, "", True, number_prefix="Exercise ")

            # Update module header immediately if all solved
            if self.is_solved():
                with self.placeholder.header:
                    _display_module_header(self.module_nr, self.title, True)
                if not self.module_session().was_solved:
                    st.balloons()
                    self.module_session().was_solved = True

        if solved or (session_solved if self.show_solved_message_by_session else False):
            # Render success message and button in the current container (fragment root)
            # instead of injecting into the external success_message container,
            # to avoid StreamlitFragmentWidgetsNotAllowedOutsideError.
            st.success("🎉 Congratulations you solved the exercise!")

            # Next Module / Solved Logic
            if self.is_solved() and self.on_module_solved_fn:
                self.on_module_solved_fn()

            # Next Level Logic
            if self.render_exercises_with_level_selectbox and len(self.exercises) > 1:
                    # Check if solved
                     if session_solved:
                         if self.jump_to_next_level and just_solved:
                              # Auto jump
                              # We need to increment level before rerunning
                              self.increment_selected_level()
                              _display_start_next_level_loading_bar()
                              st.rerun()
                         elif not self.jump_to_next_level:
                              # Manual jump button
                              if self.selected_level() < len(self.exercises):
                                   st.button("Start next level",
                                             key=f"next_level_btn_{exercise_index}",
                                             on_click=self.increment_selected_level)

        return solved

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from typing import Callable
import mr_injector.frontend.styling as styling
from mr_injector.frontend.session import ModuleSession


def get_module_styling() -> str:
    with open(Path(styling.__path__[0]) / "module.css", "r") as fp:
        text = fp.read()
    return text

def _display_module_header(module_nr: int, title: str, is_solved: bool = False, number_prefix: str = "Module "):
    if is_solved:
        checkmark = '<span class="module-status solved">&#10003;</span> <!-- Checkmark -->'
    else:
        checkmark = '<span class="module-status not-solved">&#10005;</span> <!-- "x" symbol -->'

    components.html(f"""
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
        """, height=70)


class ModuleView:
    """View class to render a exercise module"""

    def __init__(self, title: str, module_nr: int, session_key: str, render_exercises: list[Callable[[], bool | None]]):
        self.title = title
        self.module_nr = module_nr
        self.session_key = session_key
        self.render_exercises = render_exercises

        self.init_session()

        self._solved = st.session_state[self.session_key].is_solved()

    def init_session(self):
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = ModuleSession(
                num_exercises=len(self.render_exercises),
                exercise_solved={i: False for i in range(len(self.render_exercises))}
            )

    def display(self):
        try:

            with st.spinner():
                _display_module_header(self.module_nr, self.title, self._solved)
                with st.expander("Open Exercise"):
                    for i, exercise in enumerate(self.render_exercises):
                        session_solved = st.session_state[self.session_key].exercise_solved[i]
                        _display_module_header(i, "", session_solved, number_prefix="Exercise ")
                        solved = exercise()
                        if solved is True and not session_solved:
                            st.session_state[self.session_key].exercise_solved[i] = True
                        if solved or session_solved:
                            st.write("🎉 Congratulations you solved the exercise!")





        except Exception as exp:
            print(exp)
            st.error(f"Error during rendering module: {self.title}")

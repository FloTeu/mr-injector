from dataclasses import dataclass

@dataclass
class ModuleSession:
    was_solved: bool
    num_exercises: int
    exercise_solved: dict[int, bool]

    def is_solved(self):
        return all(list(self.exercise_solved.values()))
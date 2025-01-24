from pathlib import Path

from mr_injector.frontend import styling as styling


def get_exercise_styling() -> str:
    with open(Path(styling.__path__[0]) / "exercise.css", "r") as fp:
        text = fp.read()
    return text


def get_module_styling() -> str:
    with open(Path(styling.__path__[0]) / "module.css", "r") as fp:
        text = fp.read()
    return text

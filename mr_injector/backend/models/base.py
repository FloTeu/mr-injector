from enum import StrEnum


class BaseStrEnum(StrEnum):

    @classmethod
    def to_list(cls):
        return list(map(lambda c: c.value, cls))
from typing import Optional


class ImportObject:
    object: str
    alias: Optional[str] = None

    def __init__(self, object_string: str):
        if "as" in object_string:
            parts = object_string.split("as")
            self.object = parts[0].strip()
            self.alias = parts[1].strip()
        else:
            self.object = object_string.strip()

    def __hash__(self):
        return hash(f"{self.object}_{self.alias}")

    def __eq__(self, other):
        return self.object == other.object and self.alias == other.alias

    def __repr__(self):
        if self.alias is not None:
            return f"{self.object} as {self.alias}"
        else:
            return self.object

    def __str__(self):
        return self.__repr__()

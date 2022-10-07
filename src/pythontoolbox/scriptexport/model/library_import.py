from typing import List, Optional
import re

from pythontoolbox.scriptexport.model.import_object import ImportObject


class LibraryImport:
    raw_string: str
    # If there are multiple objects there can only be one library
    libraries: List[ImportObject]
    objects: List[ImportObject]

    def __init__(self, import_string: Optional[str] = None):
        self.raw_string = import_string.strip()
        self.p1 = re.compile("^import (.*)")
        self.p2 = re.compile("^from (.*) import (.*)")

        self.libraries = self.get_libraries_from_import_string(self.raw_string)
        self.objects = self.get_objects_from_import_string(self.raw_string)

    def get_libraries_from_import_string(self, import_string) -> List[ImportObject]:
        match1 = self.p1.match(import_string)
        if match1 is not None:
            return [ImportObject(obj) for obj in match1.group(1).split(",")]
        match2 = self.p2.match(import_string)
        if match2 is not None:
            return [ImportObject(match2.group(1))]
        raise Exception("Did not find library from import string")

    def get_objects_from_import_string(self, import_string) -> List[ImportObject]:
        match1 = self.p1.match(import_string)
        if match1 is not None:
            return []
        match2 = self.p2.match(import_string)
        if match2 is not None:
            return [ImportObject(obj) for obj in match2.group(2).split(",")]
        raise Exception("Did not find object match from import string")

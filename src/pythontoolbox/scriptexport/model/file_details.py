from typing import List

from pythontoolbox.scriptexport.model.library_import import LibraryImport


class FileDetails:
    path: str
    library_imports: List[LibraryImport]
    original_code_lines: [str]

    def __init__(self, path: str):
        self.path = path
        self.library_imports = []
        self.original_code_lines = []

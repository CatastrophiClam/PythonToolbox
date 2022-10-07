import re
import argparse
from typing import Optional, List, Set


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


class FileDetails:
    path: str
    library_imports: List[LibraryImport]
    original_code_lines: [str]

    def __init__(self, path: str):
        self.path = path
        self.library_imports = []
        self.original_code_lines = []


class Exporter:
    """
    Constraints:
    Can't alias local import
    We're currently importing everything from a local file if anything is imported from it
    """

    all_file_details: List[FileDetails]
    library_imports: List[str]
    code_lines: List[str]

    def __init__(self, path_to_root_file, path_to_project_root):
        self.path_to_project_root = path_to_project_root
        self.project_root = self.path_to_project_root.split("/")[-1]
        self.local_import_p1 = re.compile(f"^from {self.project_root}.* import .*")
        self.local_import_p2 = re.compile(f"^import {self.project_root}.*")
        self.library_import_p1 = re.compile("^import .*")
        self.library_import_p2 = re.compile("^from .* import .*")

        self.all_file_details: List[FileDetails] = []  # A list of file details needed, in order
        self.files_seen = set()  # Set of file paths
        self.collect_file_details(path_to_root_file)

        self.library_imports: List[str] = []
        self.collect_library_imports()

        self.code_lines: List[str] = []
        self.collect_code_lines()

    def is_local_import(self, line: str):
        if self.local_import_p1.match(line) is not None:
            return True
        if self.local_import_p2.match(line) is not None:
            return True
        return False

    def is_library_import(self, line: str):
        if self.library_import_p1.match(line) is not None:
            return True
        if self.library_import_p2.match(line) is not None:
            return True
        return False

    def get_local_import_path(self, line: str) -> str:
        """Get path to file from local import line"""
        import_parts = line.split(" ")

        chosen_part = None
        for part in import_parts:

            if self.project_root in part:
                chosen_part = part

        if chosen_part is None:
            raise Exception("Didn't find a chosen part")

        path_to_file = "/".join(chosen_part.split(".")[1:]) + ".py"
        return f"{self.path_to_project_root}/{path_to_file}"

    def collect_file_details(self, path_to_file):
        """Get fileDetails for every file needed, in order"""
        self.files_seen.add(path_to_file)
        curr_file_details = FileDetails(path_to_file)

        lines = None
        with open(path_to_file) as in_f:
            lines = in_f.readlines()

        for line in lines:
            if self.is_local_import(line):
                local_import_path = self.get_local_import_path(line)
                if local_import_path not in self.files_seen:
                    self.collect_file_details(local_import_path)
            elif self.is_library_import(line):
                curr_file_details.library_imports.append(LibraryImport(line))
            else:
                curr_file_details.original_code_lines.append(line)

        self.all_file_details.append(curr_file_details)

    def collect_library_imports(self):
        libraries_to_objects = {}
        libraries: Set[ImportObject] = set()
        for file_detail in self.all_file_details:
            for library_import in file_detail.library_imports:
                # Case of multiple objects from single library
                if len(library_import.objects) >= 1:
                    library = library_import.libraries[0].object
                    if library not in libraries_to_objects:
                        libraries_to_objects[library] = set()
                    for obj in library_import.objects:
                        libraries_to_objects[library].add(obj)
                # Case of importing 1+ libraries, no objects
                else:
                    for library_obj in library_import.libraries:
                        libraries.add(library_obj)

        for wrapped_library in libraries:
            self.library_imports.append(f"import {wrapped_library}")
        for lib_name, objects in libraries_to_objects.items():
            objects_str = ", ".join([str(obj) for obj in objects])
            self.library_imports.append(f"from {lib_name} import {objects_str}")

    def collect_code_lines(self):
        for file_detail in self.all_file_details:
            self.code_lines += file_detail.original_code_lines

    def output(self, output_path):
        with open(output_path, "w") as out_f:
            cont_empty_lines = 0

            for line in self.library_imports:
                if line == "\n":
                    cont_empty_lines += 1
                else:
                    cont_empty_lines = 0
                out_f.write(f"{line}\n")
                print(cont_empty_lines)

            while cont_empty_lines < 1:

                out_f.write("\n")
                cont_empty_lines += 1
                print(cont_empty_lines)

            for line in self.code_lines:
                if line == "\n":
                    cont_empty_lines += 1
                else:
                    cont_empty_lines = 0
                if cont_empty_lines == 3:
                    continue

                out_f.write(line)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=str)
    parser.add_argument('project_root', type=str, help="Root of imports")
    parser.add_argument('outfile', type=str, help="Output file")
    args = parser.parse_args()

    exporter = Exporter(args.infile, args.project_root)
    exporter.output(args.outfile)


if __name__ == "__main__":
    main()

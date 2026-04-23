def _filter_by_pattern(self, files: list[GDriveFile]) -> list[GDriveFile]:
        if self.file_name_pattern is None:
            return files
        elif isinstance(self.file_name_pattern, str):
            return [
                i for i in files if fnmatch.fnmatch(i["name"], self.file_name_pattern)
            ]
        else:
            return [
                i
                for i in files
                if any(
                    fnmatch.fnmatch(i["name"], pattern)
                    for pattern in self.file_name_pattern
                )
            ]
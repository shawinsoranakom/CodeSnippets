def _get_dir_vars_files(self, path: str, extensions: list[str]) -> list[str]:
        found = []
        for spath in sorted(self.list_directory(path)):
            if not spath.startswith('.') and not spath.endswith('~'):  # skip hidden and backups

                ext = os.path.splitext(spath)[-1]
                full_spath = os.path.join(path, spath)

                if self.is_directory(full_spath) and not ext:  # recursive search if dir
                    found.extend(self._get_dir_vars_files(full_spath, extensions))
                elif self.is_file(full_spath) and (not ext or ext in extensions):
                    # only consider files with valid extensions or no extension
                    found.append(full_spath)

        return found
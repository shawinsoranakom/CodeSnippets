def find_vars_files(self, path: str, name: str, extensions: list[str] | None = None, allow_dir: bool = True) -> list[str]:
        """
        Find vars files in a given path with specified name. This will find
        files in a dir named <name>/ or a file called <name> ending in known
        extensions.
        """

        jpath = os.path.join(path, name)
        found: list[str] = []

        if extensions is None:
            # Look for file with no extension first to find dir before file
            extensions = [''] + C.YAML_FILENAME_EXTENSIONS
        # add valid extensions to name
        for ext in extensions:

            if '.' in ext:
                full_path = jpath + ext
            elif ext:
                full_path = '.'.join([jpath, ext])
            else:
                full_path = jpath

            if self.path_exists(full_path):
                if self.is_directory(full_path):
                    if allow_dir:
                        found.extend(self._get_dir_vars_files(full_path, extensions))
                    else:
                        continue
                else:
                    found.append(full_path)
                break
        return found
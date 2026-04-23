def _load_role_yaml(self, subdir, main=None, allow_dir=False):
        """
        Find and load role YAML files and return data found.
        :param subdir: subdir of role to search (vars, files, tasks, handlers, defaults)
        :type subdir: string
        :param main: filename to match, will default to 'main.<ext>' if not provided.
        :type main: string
        :param allow_dir: If true we combine results of multiple matching files found.
                          If false, highlander rules. Only for vars(dicts) and not tasks(lists).
        :type allow_dir: bool

        :returns: data from the matched file(s), type can be dict or list depending on vars or tasks.
        """
        data = None
        file_path = os.path.join(self._role_path, subdir)
        if self._loader.path_exists(file_path) and self._loader.is_directory(file_path):
            # Valid extensions and ordering for roles is hard-coded to maintain portability
            extensions = ['.yml', '.yaml', '.json']  # same as default for YAML_FILENAME_EXTENSIONS

            # look for files w/o extensions before/after bare name depending on it being set or not
            # keep 'main' as original to figure out errors if no files found
            if main is None:
                _main = 'main'
                extensions.append('')
            else:
                _main = main
                extensions.insert(0, '')

            # not really 'find_vars_files' but find_files_with_extensions_default_to_yaml_filename_extensions
            found_files = self._loader.find_vars_files(file_path, _main, extensions, allow_dir)
            if found_files:
                for found in found_files:

                    if not is_subpath(found, file_path):
                        raise self._FAIL(f"Failed loading '{found!r}' for role ({self._role_name}) "
                                         f"as it is not inside the expected role path: {file_path!r}")

                    new_data = self._loader.load_from_file(found, trusted_as_template=True)
                    if new_data:
                        if data is not None and isinstance(new_data, Mapping):
                            data = combine_vars(data, new_data)
                        else:
                            data = new_data

                        # found data so no need to continue unless we want to merge
                        if not allow_dir:
                            break

            elif main is not None:
                # this won't trigger with default only when <subdir>_from is specified
                raise self._FAIL(f"Could not find specified file in role: {subdir}/{main}")
        elif main is not None:
            # this won't trigger with default only when <subdir>_from is specified
            raise self._FAIL(f"Could not find specified file in role, its '{subdir}/' is not usable.")

        return data
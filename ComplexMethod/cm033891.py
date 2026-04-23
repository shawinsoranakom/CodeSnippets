def _process_terms(self, terms: c.Sequence, variables: dict[str, t.Any]) -> list[str]:

        total_search = []

        # can use a dict instead of list item to pass inline config
        for term in terms:
            if isinstance(term, c.Mapping):
                self.set_options(var_options=variables, direct=term)
                files = self.get_option('files')
                files_description = "the 'files' option"
            elif isinstance(term, str):
                files = [term]
                files_description = "files"
            elif isinstance(term, c.Sequence):
                partial = self._process_terms(term, variables)
                total_search.extend(partial)
                continue
            else:
                raise AnsibleError(f"Invalid term supplied. A string, dict or list is required, not {native_type_name(term)!r}).")

            paths = self.get_option('paths')

            # magic extra splitting to create lists
            filelist = _split_on(files_description, files, ',;')
            pathlist = _split_on('the "paths" option', paths, ',:;')

            # create search structure
            if pathlist:
                for path in pathlist:
                    for fn in filelist:
                        f = os.path.join(path, fn)
                        total_search.append(f)
            else:
                # NOTE: this is now 'extend', previously it would clobber all options, but we deemed that a bug
                total_search.extend(filelist)

        return total_search
def path_dwim_relative_stack(self, paths: list[str], dirname: str | None, source: str | None, is_role: bool = False) -> str:
        """
        find one file in first path in stack taking roles into account and adding play basedir as fallback

        :arg paths: A list of text strings which are the paths to look for the filename in.
        :arg dirname: A text string representing a directory.  The directory
            is prepended to the source to form the path to search for.
        :arg source: A text string which is the filename to search for
        :rtype: A text string
        :returns: An absolute path to the filename ``source`` if found
        :raises: An AnsibleFileNotFound Exception if the file is found to exist in the search paths
        """
        source_root = None
        if source:
            source_root = source.split('/')[0]
        basedir = self.get_basedir()
        result = None
        search = []
        if source is None:
            display.warning('Invalid request to find a file that matches a "null" value')
        elif source and (source.startswith('~') or source.startswith(os.path.sep)):
            # path is absolute, no relative needed, check existence and return source
            test_path = unfrackpath(source, follow=False)
            if os.path.exists(test_path):
                result = test_path
        else:
            display.debug('evaluation_path:\n\t%s' % '\n\t'.join(paths))
            for path in paths:
                upath = unfrackpath(path, follow=False)
                pb_base_dir = os.path.dirname(upath)

                # if path is in role and 'tasks' not there already, add it into the search
                if (is_role or self._is_role(path)) and pb_base_dir.endswith('/tasks'):
                    if dirname:
                        search.append(os.path.join(os.path.dirname(pb_base_dir), dirname, source))
                    search.append(os.path.join(pb_base_dir, source))
                # don't add dirname if user already is using it in source
                if dirname and source_root != dirname:
                    search.append(os.path.join(upath, dirname, source))
                search.append(os.path.join(upath, source))

            # always append basedir as last resort
            # don't add dirname if user already is using it in source
            if dirname and source_root != dirname:
                search.append(os.path.join(basedir, dirname, source))
            search.append(os.path.join(basedir, source))

            display.debug('search_path:\n\t%s' % '\n\t'.join(search))
            for candidate in search:
                display.vvvvv('looking for "%s" at "%s"' % (source, candidate))
                if os.path.exists(candidate):
                    result = candidate
                    break

        if result is None:
            raise AnsibleFileNotFound(file_name=source, paths=search)

        return result
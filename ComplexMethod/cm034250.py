def path_dwim_relative(self, path: str, dirname: str, source: str, is_role: bool = False) -> str:
        """
        find one file in either a role or playbook dir with or without
        explicitly named dirname subdirs

        Used in action plugins and lookups to find supplemental files that
        could be in either place.
        """

        search = []

        # I have full path, nothing else needs to be looked at
        if source.startswith(os.path.sep) or source.startswith('~'):
            search.append(unfrackpath(source, follow=False))
        else:
            # base role/play path + templates/files/vars + relative filename
            search.append(os.path.join(path, dirname, source))
            basedir = unfrackpath(path, follow=False)

            # not told if role, but detect if it is a role and if so make sure you get correct base path
            if not is_role:
                is_role = self._is_role(path)

            if is_role and RE_TASKS.search(path):
                basedir = unfrackpath(os.path.dirname(path), follow=False)

            cur_basedir = self._basedir
            self.set_basedir(basedir)
            # resolved base role/play path + templates/files/vars + relative filename
            search.append(unfrackpath(os.path.join(basedir, dirname, source), follow=False))
            self.set_basedir(cur_basedir)

            if is_role and not source.endswith(dirname):
                # look in role's tasks dir w/o dirname
                search.append(unfrackpath(os.path.join(basedir, 'tasks', source), follow=False))

            # try to create absolute path for loader basedir + templates/files/vars + filename
            search.append(unfrackpath(os.path.join(dirname, source), follow=False))

            # try to create absolute path for loader basedir
            search.append(unfrackpath(os.path.join(basedir, source), follow=False))

            # try to create absolute path for  dirname + filename
            search.append(self.path_dwim(os.path.join(dirname, source)))

            # try to create absolute path for filename
            search.append(self.path_dwim(source))

        for candidate in search:
            if os.path.exists(candidate):
                break

        return candidate
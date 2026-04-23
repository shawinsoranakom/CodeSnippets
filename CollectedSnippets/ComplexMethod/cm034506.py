def files_in_archive(self):
        if self._files_in_archive:
            return self._files_in_archive

        self._files_in_archive = []
        try:
            archive = ZipFile(self.src)
        except BadZipFile as e:
            if e.args[0].lower().startswith('bad magic number'):
                # Python2.4 can't handle zipfiles with > 64K files.  Try using
                # /usr/bin/unzip instead
                self._legacy_file_list()
            else:
                raise
        else:
            try:
                for member in archive.namelist():
                    if self.include_files:
                        for include in self.include_files:
                            if fnmatch.fnmatch(member, include):
                                self._files_in_archive.append(to_native(member))
                    else:
                        exclude_flag = False
                        if self.excludes:
                            for exclude in self.excludes:
                                if fnmatch.fnmatch(member, exclude):
                                    exclude_flag = True
                                    break
                        if not exclude_flag:
                            self._files_in_archive.append(to_native(member))
            except Exception as e:
                archive.close()
                raise UnarchiveError('Unable to list files in the archive: %s' % to_native(e))

            archive.close()
        return self._files_in_archive
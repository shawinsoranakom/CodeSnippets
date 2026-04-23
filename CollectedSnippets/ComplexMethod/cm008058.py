def update(self, update_info=NO_DEFAULT):
        """Update yt-dlp executable to the latest version
        @param update_info  `UpdateInfo | None` as returned by query_update()
        """
        if update_info is NO_DEFAULT:
            update_info = self.query_update(_output=True)
        if not update_info:
            return False

        err = is_non_updateable()
        if err:
            self._report_error(err, True)
            return False

        self.ydl.to_screen(f'Current Build Hash: {_sha256_file(self.filename)}')

        update_label = _make_label(self.requested_repo, update_info.tag, update_info.version)
        self.ydl.to_screen(f'Updating to {update_label} ...')

        directory = os.path.dirname(self.filename)
        if not os.access(self.filename, os.W_OK):
            return self._report_permission_error(self.filename)
        elif not os.access(directory, os.W_OK):
            return self._report_permission_error(directory)

        new_filename, old_filename = f'{self.filename}.new', f'{self.filename}.old'
        if detect_variant() == 'zip':  # Can be replaced in-place
            new_filename, old_filename = self.filename, None

        try:
            if os.path.exists(old_filename or ''):
                os.remove(old_filename)
        except OSError:
            return self._report_error('Unable to remove the old version')

        try:
            newcontent = self._download_asset(update_info.binary_name, update_info.tag)
        except network_exceptions as e:
            if isinstance(e, HTTPError) and e.status == 404:
                return self._report_error(
                    f'The requested tag {self.requested_repo}@{update_info.tag} does not exist', True)
            return self._report_network_error(f'fetch updates: {e}', tag=update_info.tag)

        if not update_info.checksum:
            self._block_restart('Automatically restarting into unverified builds is disabled for security reasons')
        elif hashlib.sha256(newcontent).hexdigest() != update_info.checksum:
            return self._report_network_error('verify the new executable', tag=update_info.tag)

        try:
            with open(new_filename, 'wb') as outf:
                outf.write(newcontent)
        except OSError:
            return self._report_permission_error(new_filename)

        if old_filename:
            mask = os.stat(self.filename).st_mode
            try:
                os.rename(self.filename, old_filename)
            except OSError:
                return self._report_error('Unable to move current version')

            try:
                os.rename(new_filename, self.filename)
            except OSError:
                self._report_error('Unable to overwrite current version')
                return os.rename(old_filename, self.filename)

        variant = detect_variant()
        if variant.startswith('win'):
            atexit.register(Popen, f'ping 127.0.0.1 -n 5 -w 1000 & del /F "{old_filename}"',
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif old_filename:
            try:
                os.remove(old_filename)
            except OSError:
                self._report_error('Unable to remove the old version')

            try:
                os.chmod(self.filename, mask)
            except OSError:
                return self._report_error(
                    f'Unable to set permissions. Run: sudo chmod a+rx {shell_quote(self.filename)}')

        self.ydl.to_screen(f'Updated yt-dlp to {update_label}')
        return True
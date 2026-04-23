def query_update(self, *, _output=False) -> UpdateInfo | None:
        """Fetches info about the available update
        @returns   An `UpdateInfo` if there is an update available, else None
        """
        if not self.requested_repo:
            self._report_error('No target repository could be determined from input')
            return None

        try:
            requested_version, target_commitish = self._get_version_info(self.requested_tag)
        except network_exceptions as e:
            self._report_network_error(f'obtain version info ({e})', delim='; Please try again later or')
            return None

        if self._exact and self._origin != self.requested_repo:
            has_update = True
        elif requested_version:
            if self._exact:
                has_update = self.current_version != requested_version
            else:
                has_update = not self._version_compare(self.current_version, requested_version)
        elif target_commitish:
            has_update = target_commitish != self.current_commit
        else:
            has_update = False

        resolved_tag = requested_version if self.requested_tag == 'latest' else self.requested_tag
        current_label = _make_label(self._origin, self._channel.partition('@')[2] or self.current_version, self.current_version)
        requested_label = _make_label(self.requested_repo, resolved_tag, requested_version)
        latest_or_requested = f'{"Latest" if self.requested_tag == "latest" else "Requested"} version: {requested_label}'
        if not has_update:
            if _output:
                self.ydl.to_screen(f'{latest_or_requested}\nyt-dlp is up to date ({current_label})')
            return None

        update_spec = self._download_update_spec(('latest', None) if requested_version else (None,))
        if not update_spec:
            return None
        # `result_` prefixed vars == post-_process_update_spec() values
        result_tag = self._process_update_spec(update_spec, resolved_tag)
        if not result_tag or result_tag == self.current_version:
            return None
        elif result_tag == resolved_tag:
            result_version = requested_version
        elif _VERSION_RE.fullmatch(result_tag):
            result_version = result_tag
        else:  # actual version being updated to is unknown
            result_version = None

        checksum = None
        # Non-updateable variants can get update_info but need to skip checksum
        if not is_non_updateable():
            try:
                hashes = self._download_asset('SHA2-256SUMS', result_tag)
            except network_exceptions as error:
                if not isinstance(error, HTTPError) or error.status != 404:
                    self._report_network_error(f'fetch checksums: {error}')
                    return None
                self.ydl.report_warning('No hash information found for the release, skipping verification')
            else:
                for ln in hashes.decode().splitlines():
                    if ln.endswith(_get_binary_name()):
                        checksum = ln.split()[0]
                        break
                if not checksum:
                    self.ydl.report_warning('The hash could not be found in the checksum file, skipping verification')

        if _output:
            update_label = _make_label(self.requested_repo, result_tag, result_version)
            self.ydl.to_screen(
                f'Current version: {current_label}\n{latest_or_requested}'
                + (f'\nUpgradable to: {update_label}' if update_label != requested_label else ''))

        return UpdateInfo(
            tag=result_tag,
            version=result_version,
            requested_version=requested_version,
            commit=target_commitish if result_tag == resolved_tag else None,
            checksum=checksum)
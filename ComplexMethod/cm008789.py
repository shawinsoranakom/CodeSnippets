def _call_downloader(self, tmpfilename, info_dict):
        """ Either overwrite this or implement _make_cmd """
        cmd = [encodeArgument(a) for a in self._make_cmd(tmpfilename, info_dict)]

        self._debug_cmd(cmd)

        if 'fragments' not in info_dict:
            _, stderr, returncode = self._call_process(cmd, info_dict)
            if returncode and stderr:
                self.to_stderr(stderr)
            return returncode

        skip_unavailable_fragments = self.params.get('skip_unavailable_fragments', True)

        retry_manager = RetryManager(self.params.get('fragment_retries'), self.report_retry,
                                     frag_index=None, fatal=not skip_unavailable_fragments)
        for retry in retry_manager:
            _, stderr, returncode = self._call_process(cmd, info_dict)
            if not returncode:
                break
            # TODO: Decide whether to retry based on error code
            # https://aria2.github.io/manual/en/html/aria2c.html#exit-status
            if stderr:
                self.to_stderr(stderr)
            retry.error = Exception()
            continue
        if not skip_unavailable_fragments and retry_manager.error:
            return -1

        decrypt_fragment = self.decrypter(info_dict)
        dest, _ = self.sanitize_open(tmpfilename, 'wb')
        for frag_index, fragment in enumerate(info_dict['fragments']):
            fragment_filename = f'{tmpfilename}-Frag{frag_index}'
            try:
                src, _ = self.sanitize_open(fragment_filename, 'rb')
            except OSError as err:
                if skip_unavailable_fragments and frag_index > 1:
                    self.report_skip_fragment(frag_index, err)
                    continue
                self.report_error(f'Unable to open fragment {frag_index}; {err}')
                return -1
            dest.write(decrypt_fragment(fragment, src.read()))
            src.close()
            if not self.params.get('keep_fragments', False):
                self.try_remove(fragment_filename)
        dest.close()
        self.try_remove(f'{tmpfilename}.frag.urls')
        return 0
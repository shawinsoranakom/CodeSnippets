def dl(self, name, info, subtitle=False, test=False):
        if not info.get('url'):
            self.raise_no_formats(info, True)

        if test:
            verbose = self.params.get('verbose')
            quiet = self.params.get('quiet') or not verbose
            params = {
                'test': True,
                'quiet': quiet,
                'verbose': verbose,
                'noprogress': quiet,
                'nopart': True,
                'skip_unavailable_fragments': False,
                'keep_fragments': False,
                'overwrites': True,
                '_no_ytdl_file': True,
            }
        else:
            params = self.params

        fd = get_suitable_downloader(info, params, to_stdout=(name == '-'))(self, params)
        if not test:
            for ph in self._progress_hooks:
                fd.add_progress_hook(ph)
            urls = '", "'.join(
                (f['url'].split(',')[0] + ',<data>' if f['url'].startswith('data:') else f['url'])
                for f in info.get('requested_formats', []) or [info])
            self.write_debug(f'Invoking {fd.FD_NAME} downloader on "{urls}"')

        # Note: Ideally info should be a deep-copied so that hooks cannot modify it.
        # But it may contain objects that are not deep-copyable
        new_info = self._copy_infodict(info)
        if new_info.get('http_headers') is None:
            new_info['http_headers'] = self._calc_headers(new_info)
        return fd.download(name, new_info, subtitle)
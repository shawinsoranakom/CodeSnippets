def download(self, filename, info_dict, subtitle=False):
        """Download to a filename using the info from info_dict
        Return True on success and False otherwise
        """
        nooverwrites_and_exists = (
            not self.params.get('overwrites', True)
            and os.path.exists(filename)
        )

        if not hasattr(filename, 'write'):
            continuedl_and_exists = (
                self.params.get('continuedl', True)
                and os.path.isfile(filename)
                and not self.params.get('nopart', False)
            )

            # Check file already present
            if filename != '-' and (nooverwrites_and_exists or continuedl_and_exists):
                self.report_file_already_downloaded(filename)
                self._hook_progress({
                    'filename': filename,
                    'status': 'finished',
                    'total_bytes': os.path.getsize(filename),
                }, info_dict)
                self._finish_multiline_status()
                return True, False

        sleep_note = ''
        if subtitle:
            sleep_interval = self.params.get('sleep_interval_subtitles') or 0
        else:
            min_sleep_interval = self.params.get('sleep_interval') or 0
            max_sleep_interval = self.params.get('max_sleep_interval') or 0

            requested_formats = info_dict.get('requested_formats') or [info_dict]
            if available_at := max(f.get('available_at') or 0 for f in requested_formats):
                forced_sleep_interval = available_at - int(time.time())
                if forced_sleep_interval > min_sleep_interval:
                    sleep_note = 'as required by the site'
                    min_sleep_interval = forced_sleep_interval
                if forced_sleep_interval > max_sleep_interval:
                    max_sleep_interval = forced_sleep_interval

            sleep_interval = random.uniform(
                min_sleep_interval, max_sleep_interval or min_sleep_interval)

        if sleep_interval > 0:
            self.to_screen(f'[download] Sleeping {sleep_interval:.2f} seconds {sleep_note}...')
            time.sleep(sleep_interval)

        ret = self.real_download(filename, info_dict)
        self._finish_multiline_status()
        return ret, True
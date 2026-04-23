def download(self, filename, info_dict):
        """Download to a filename using the info from info_dict
        Return True on success and False otherwise

        This method filters the `Cookie` header from the info_dict to prevent leaks.
        Downloaders have their own way of handling cookies.
        See: https://github.com/yt-dlp/yt-dlp/security/advisories/GHSA-v8mc-9377-rwjj
        """

        nooverwrites_and_exists = (
            self.params.get('nooverwrites', False)
            and os.path.exists(encodeFilename(filename))
        )

        if not hasattr(filename, 'write'):
            continuedl_and_exists = (
                self.params.get('continuedl', True)
                and os.path.isfile(encodeFilename(filename))
                and not self.params.get('nopart', False)
            )

            # Check file already present
            if filename != '-' and (nooverwrites_and_exists or continuedl_and_exists):
                self.report_file_already_downloaded(filename)
                self._hook_progress({
                    'filename': filename,
                    'status': 'finished',
                    'total_bytes': os.path.getsize(encodeFilename(filename)),
                })
                return True

        min_sleep_interval, max_sleep_interval = (
            float_or_none(self.params.get(interval), default=0)
            for interval in ('sleep_interval', 'max_sleep_interval'))

        sleep_note = ''
        available_at = info_dict.get('available_at')
        if available_at:
            forced_sleep_interval = available_at - int(time.time())
            if forced_sleep_interval > min_sleep_interval:
                sleep_note = 'as required by the site'
                min_sleep_interval = forced_sleep_interval
            if forced_sleep_interval > max_sleep_interval:
                max_sleep_interval = forced_sleep_interval

        sleep_interval = random.uniform(
            min_sleep_interval, max_sleep_interval or min_sleep_interval)

        if sleep_interval > 0:
            self.to_screen(
                '[download] Sleeping %.2f seconds %s...' % (
                    sleep_interval, sleep_note))
            time.sleep(sleep_interval)

        return self.real_download(filename, info_dict)
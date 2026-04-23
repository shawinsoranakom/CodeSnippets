def _write_subtitles(self, info_dict, filename):
        """ Write subtitles to file and return list of (sub_filename, final_sub_filename); or None if error"""
        ret = []
        subtitles = info_dict.get('requested_subtitles')
        if not (self.params.get('writesubtitles') or self.params.get('writeautomaticsub')):
            # subtitles download errors are already managed as troubles in relevant IE
            # that way it will silently go on when used with unsupporting IE
            return ret
        elif not subtitles:
            self.to_screen('[info] There are no subtitles for the requested languages')
            return ret
        sub_filename_base = self.prepare_filename(info_dict, 'subtitle')
        if not sub_filename_base:
            self.to_screen('[info] Skipping writing video subtitles')
            return ret

        for sub_lang, sub_info in subtitles.items():
            sub_format = sub_info['ext']
            sub_filename = subtitles_filename(filename, sub_lang, sub_format, info_dict.get('ext'))
            sub_filename_final = subtitles_filename(sub_filename_base, sub_lang, sub_format, info_dict.get('ext'))
            existing_sub = self.existing_file((sub_filename_final, sub_filename))
            if existing_sub:
                self.to_screen(f'[info] Video subtitle {sub_lang}.{sub_format} is already present')
                sub_info['filepath'] = existing_sub
                ret.append((existing_sub, sub_filename_final))
                continue

            self.to_screen(f'[info] Writing video subtitles to: {sub_filename}')
            if sub_info.get('data') is not None:
                try:
                    # Use newline='' to prevent conversion of newline characters
                    # See https://github.com/ytdl-org/youtube-dl/issues/10268
                    with open(sub_filename, 'w', encoding='utf-8', newline='') as subfile:
                        subfile.write(sub_info['data'])
                    sub_info['filepath'] = sub_filename
                    ret.append((sub_filename, sub_filename_final))
                    continue
                except OSError:
                    self.report_error(f'Cannot write video subtitles file {sub_filename}')
                    return None

            try:
                sub_copy = sub_info.copy()
                sub_copy.setdefault('http_headers', info_dict.get('http_headers'))
                self.dl(sub_filename, sub_copy, subtitle=True)
                sub_info['filepath'] = sub_filename
                ret.append((sub_filename, sub_filename_final))
            except (DownloadError, ExtractorError, OSError, ValueError, *network_exceptions) as err:
                msg = f'Unable to download video subtitles for {sub_lang!r}: {err}'
                if self.params.get('ignoreerrors') is not True:  # False or 'only_download'
                    if not self.params.get('ignoreerrors'):
                        self.report_error(msg)
                    raise DownloadError(msg)
                self.report_warning(msg)
        return ret
def _match_entry(self, info_dict, incomplete=False, silent=False):
        """Returns None if the file should be downloaded"""
        _type = 'video' if 'playlist-match-filter' in self.params['compat_opts'] else info_dict.get('_type', 'video')
        assert incomplete or _type == 'video', 'Only video result can be considered complete'

        video_title = info_dict.get('title', info_dict.get('id', 'entry'))

        def check_filter():
            if _type in ('playlist', 'multi_video'):
                return
            elif _type in ('url', 'url_transparent') and not try_call(
                    lambda: self.get_info_extractor(info_dict['ie_key']).is_single_video(info_dict['url'])):
                return

            if 'title' in info_dict:
                # This can happen when we're just evaluating the playlist
                title = info_dict['title']
                matchtitle = self.params.get('matchtitle', False)
                if matchtitle:
                    if not re.search(matchtitle, title, re.IGNORECASE):
                        return '"' + title + '" title did not match pattern "' + matchtitle + '"'
                rejecttitle = self.params.get('rejecttitle', False)
                if rejecttitle:
                    if re.search(rejecttitle, title, re.IGNORECASE):
                        return '"' + title + '" title matched reject pattern "' + rejecttitle + '"'

            date = info_dict.get('upload_date')
            if date is not None:
                date_range = self.params.get('daterange', DateRange())
                if date not in date_range:
                    return f'{date_from_str(date).isoformat()} upload date is not in range {date_range}'
            view_count = info_dict.get('view_count')
            if view_count is not None:
                min_views = self.params.get('min_views')
                if min_views is not None and view_count < min_views:
                    return 'Skipping %s, because it has not reached minimum view count (%d/%d)' % (video_title, view_count, min_views)
                max_views = self.params.get('max_views')
                if max_views is not None and view_count > max_views:
                    return 'Skipping %s, because it has exceeded the maximum view count (%d/%d)' % (video_title, view_count, max_views)
            if age_restricted(info_dict.get('age_limit'), self.params.get('age_limit')):
                return f'Skipping "{video_title}" because it is age restricted'

            match_filter = self.params.get('match_filter')
            if match_filter is None:
                return None

            cancelled = None
            try:
                try:
                    ret = match_filter(info_dict, incomplete=incomplete)
                except TypeError:
                    # For backward compatibility
                    ret = None if incomplete else match_filter(info_dict)
            except DownloadCancelled as err:
                if err.msg is not NO_DEFAULT:
                    raise
                ret, cancelled = err.msg, err

            if ret is NO_DEFAULT:
                while True:
                    filename = self._format_screen(self.prepare_filename(info_dict), self.Styles.FILENAME)
                    self.to_screen(
                        self._format_screen(f'Download "{filename}"? (Y/n): ', self.Styles.EMPHASIS),
                        skip_eol=True)
                    reply = input().lower().strip()
                    if reply in {'y', ''}:
                        return None
                    elif reply == 'n':
                        if cancelled:
                            raise type(cancelled)(f'Skipping {video_title}')
                        return f'Skipping {video_title}'
            return ret

        if self.in_download_archive(info_dict):
            reason = ''.join((
                format_field(info_dict, 'id', f'{self._format_screen("%s", self.Styles.ID)}: '),
                format_field(info_dict, 'title', f'{self._format_screen("%s", self.Styles.EMPHASIS)} '),
                'has already been recorded in the archive'))
            break_opt, break_err = 'break_on_existing', ExistingVideoReached
        else:
            try:
                reason = check_filter()
            except DownloadCancelled as e:
                reason, break_opt, break_err = e.msg, 'match_filter', type(e)
            else:
                break_opt, break_err = 'break_on_reject', RejectedVideoReached
        if reason is not None:
            if not silent:
                self.to_screen('[download] ' + reason)
            if self.params.get(break_opt, False):
                raise break_err()
        return reason
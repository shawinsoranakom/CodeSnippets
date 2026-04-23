def _wait_for_video(self, ie_result={}):
        if (not self.params.get('wait_for_video')
                or ie_result.get('_type', 'video') != 'video'
                or ie_result.get('formats') or ie_result.get('url')):
            return

        format_dur = lambda dur: '%02d:%02d:%02d' % timetuple_from_msec(dur * 1000)[:-1]
        last_msg = ''

        def progress(msg):
            nonlocal last_msg
            full_msg = f'{msg}\n'
            if not self.params.get('noprogress'):
                full_msg = msg + ' ' * (len(last_msg) - len(msg)) + '\r'
            elif last_msg:
                return
            self.to_screen(full_msg, skip_eol=True)
            last_msg = msg

        min_wait, max_wait = self.params.get('wait_for_video')
        diff = try_get(ie_result, lambda x: x['release_timestamp'] - time.time())
        if diff is None and ie_result.get('live_status') == 'is_upcoming':
            diff = round(random.uniform(min_wait, max_wait) if (max_wait and min_wait) else (max_wait or min_wait), 0)
            self.report_warning('Release time of video is not known')
        elif ie_result and (diff or 0) <= 0:
            self.report_warning('Video should already be available according to extracted info')
        diff = min(max(diff or 0, min_wait or 0), max_wait or float('inf'))
        self.to_screen(f'[wait] Waiting for {format_dur(diff)} - Press Ctrl+C to try now')

        wait_till = time.time() + diff
        try:
            while True:
                diff = wait_till - time.time()
                if diff <= 0:
                    progress('')
                    raise ReExtractInfo('[wait] Wait period ended', expected=True)
                progress(f'[wait] Remaining time until next attempt: {self._format_screen(format_dur(diff), self.Styles.EMPHASIS)}')
                time.sleep(1)
        except KeyboardInterrupt:
            progress('')
            raise ReExtractInfo('[wait] Interrupted by user', expected=True)
        except BaseException as e:
            if not isinstance(e, ReExtractInfo):
                self.to_screen('')
            raise
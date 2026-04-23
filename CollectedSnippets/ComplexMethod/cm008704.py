def _live_dash_fragments(self, video_id, itag, client_name, live_start_time, mpd_feed, manifestless_orig_fmt, ctx):
        FETCH_SPAN, MAX_DURATION = 5, 432000

        mpd_url, stream_number, is_live = None, None, True

        begin_index = 0
        download_start_time = ctx.get('start') or time.time()

        lack_early_segments = download_start_time - (live_start_time or download_start_time) > MAX_DURATION
        if lack_early_segments:
            self.report_warning(bug_reports_message(
                'Starting download from the last 120 hours of the live stream since '
                'YouTube does not have data before that. If you think this is wrong,'), only_once=True)
            lack_early_segments = True

        known_idx, no_fragment_score, last_segment_url = begin_index, 0, None
        fragments, fragment_base_url = None, None

        def _extract_sequence_from_mpd(refresh_sequence, immediate):
            nonlocal mpd_url, stream_number, is_live, no_fragment_score, fragments, fragment_base_url
            # Obtain from MPD's maximum seq value
            old_mpd_url = mpd_url
            last_error = ctx.pop('last_error', None)
            expire_fast = immediate or (last_error and isinstance(last_error, HTTPError) and last_error.status == 403)
            mpd_url, stream_number, is_live = (mpd_feed(itag, client_name, 5 if expire_fast else 18000)
                                               or (mpd_url, stream_number, False))
            if not refresh_sequence:
                if expire_fast and not is_live:
                    return False, last_seq
                elif old_mpd_url == mpd_url:
                    return True, last_seq
            if manifestless_orig_fmt:
                fmt_info = manifestless_orig_fmt
            else:
                try:
                    fmts, _ = self._extract_mpd_formats_and_subtitles(
                        mpd_url, None, note=False, errnote=False, fatal=False)
                except ExtractorError:
                    fmts = None
                if not fmts:
                    no_fragment_score += 2
                    return False, last_seq
                fmt_info = next(x for x in fmts if x['manifest_stream_number'] == stream_number)
            fragments = fmt_info['fragments']
            fragment_base_url = fmt_info['fragment_base_url']
            assert fragment_base_url

            _last_seq = int(re.search(r'(?:/|^)sq/(\d+)', fragments[-1]['path']).group(1))
            return True, _last_seq

        self.write_debug(f'[{video_id}] Generating fragments for format {itag}')
        while is_live:
            fetch_time = time.time()
            if no_fragment_score > 30:
                return
            if last_segment_url:
                # Obtain from "X-Head-Seqnum" header value from each segment
                try:
                    urlh = self._request_webpage(
                        last_segment_url, None, note=False, errnote=False, fatal=False)
                except ExtractorError:
                    urlh = None
                last_seq = try_get(urlh, lambda x: int_or_none(x.headers['X-Head-Seqnum']))
                if last_seq is None:
                    no_fragment_score += 2
                    last_segment_url = None
                    continue
            else:
                should_continue, last_seq = _extract_sequence_from_mpd(True, no_fragment_score > 15)
                no_fragment_score += 2
                if not should_continue:
                    continue

            if known_idx > last_seq:
                last_segment_url = None
                continue

            last_seq += 1

            if begin_index < 0 and known_idx < 0:
                # skip from the start when it's negative value
                known_idx = last_seq + begin_index
            if lack_early_segments:
                known_idx = max(known_idx, last_seq - int(MAX_DURATION // fragments[-1]['duration']))
            try:
                for idx in range(known_idx, last_seq):
                    # do not update sequence here or you'll get skipped some part of it
                    should_continue, _ = _extract_sequence_from_mpd(False, False)
                    if not should_continue:
                        known_idx = idx - 1
                        raise ExtractorError('breaking out of outer loop')
                    last_segment_url = urljoin(fragment_base_url, f'sq/{idx}')
                    yield {
                        'url': last_segment_url,
                        'fragment_count': last_seq,
                    }
                if known_idx == last_seq:
                    no_fragment_score += 5
                else:
                    no_fragment_score = 0
                known_idx = last_seq
            except ExtractorError:
                continue

            if manifestless_orig_fmt:
                # Stop at the first iteration if running for post-live manifestless;
                # fragment count no longer increase since it starts
                break

            time.sleep(max(0, FETCH_SPAN + fetch_time - time.time()))
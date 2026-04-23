def _extract_video(self, video_id, segment_id):
        # Not a segmented episode: return single video
        # Segmented episode without valid segment id: return entire playlist
        # Segmented episode with valid segment id and yes-playlist: return entire playlist
        # Segmented episode with valid segment id and no-playlist: return single video corresponding to segment id
        # If a multi_video playlist would be returned, but an unsegmented source exists, that source is chosen instead.

        api_json = self._call_api(video_id)

        if traverse_obj(api_json, 'is_drm_protected'):
            self.report_drm(video_id)

        # updates formats, subtitles
        def extract_sources(src_json, video_id):
            for manifest_type in traverse_obj(src_json, ('sources', T(dict.keys), Ellipsis)):
                for manifest_url in traverse_obj(src_json, ('sources', manifest_type, Ellipsis, 'src', T(url_or_none))):
                    if manifest_type == 'hls':
                        fmts, subs = self._extract_m3u8_formats(
                            manifest_url, video_id, fatal=False, m3u8_id='hls',
                            ext='mp4', entry_protocol='m3u8_native'), {}
                        for f in fmts:
                            if '_vo.' in f['url']:
                                f['acodec'] = 'none'
                    elif manifest_type == 'dash':
                        fmts, subs = self._extract_mpd_formats_and_subtitles(
                            manifest_url, video_id, fatal=False, mpd_id='dash')
                    else:
                        continue
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)

        formats, subtitles = [], {}
        if segment_id is None:
            extract_sources(api_json, video_id)
        if not formats:
            segments = traverse_obj(api_json, (
                '_embedded', 'segments', lambda _, v: v['id']))
            if len(segments) > 1 and segment_id is not None:
                if not self._yes_playlist(video_id, segment_id, playlist_label='collection', video_label='segment'):
                    segments = [next(s for s in segments if txt_or_none(s['id']) == segment_id)]

            entries = []
            for seg in segments:
                formats, subtitles = [], {}
                extract_sources(seg, segment_id)
                self._sort_formats(formats)
                entries.append(merge_dicts({
                    'formats': formats,
                    'subtitles': subtitles,
                }, self._parse_metadata(seg), rev=True))
            result = merge_dicts(
                {'_type': 'multi_video' if len(entries) > 1 else 'playlist'},
                self._parse_metadata(api_json),
                self.playlist_result(entries, video_id))
            # not yet processed in core for playlist/multi
            self._downloader._fill_common_fields(result)
            return result
        else:
            self._sort_formats(formats)

        for sub_url in traverse_obj(api_json, (
                '_embedded', 'subtitle',
                ('xml_url', 'sami_url', 'stl_url', 'ttml_url', 'srt_url', 'vtt_url'),
                T(url_or_none))):
            self._merge_subtitles({'de': [{'url': sub_url}]}, target=subtitles)

        return merge_dicts({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            # '_old_archive_ids': [self._downloader._make_archive_id({'ie_key': 'ORFTVthek', 'id': video_id})],
        }, self._parse_metadata(api_json), rev=True)
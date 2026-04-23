def _get_anvato_videos(self, access_key, video_id, token):
        video_data = self._get_video_json(access_key, video_id, token)

        formats = []
        for published_url in video_data['published_urls']:
            video_url = published_url.get('embed_url')
            if not video_url:
                continue
            media_format = published_url.get('format')
            ext = determine_ext(video_url)

            if ext == 'smil' or media_format == 'smil':
                formats.extend(self._extract_smil_formats(video_url, video_id))
                continue

            tbr = int_or_none(published_url.get('kbps'))
            a_format = {
                'url': video_url,
                'format_id': join_nonempty('http', published_url.get('cdn_name')).lower(),
                'tbr': tbr or None,
            }

            vtt_subs, hls_subs = {}, {}
            if media_format == 'vtt':
                _, vtt_subs = self._extract_m3u8_formats_and_subtitles(
                    video_url, video_id, m3u8_id='vtt', fatal=False)
                continue
            elif media_format == 'm3u8' and tbr is not None:
                a_format.update({
                    'format_id': join_nonempty('hls', tbr),
                    'ext': 'mp4',
                })
            elif media_format == 'm3u8-variant' or ext == 'm3u8':
                # For some videos the initial m3u8 URL returns JSON instead
                manifest_json = self._download_json(
                    video_url, video_id, note='Downloading manifest JSON', fatal=False)
                if manifest_json:
                    video_url = manifest_json.get('master_m3u8')
                    if not video_url:
                        continue
                hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                    video_url, video_id, ext='mp4', m3u8_id='hls', fatal=False)
                formats.extend(hls_fmts)
                continue
            elif ext == 'mp3' or media_format == 'mp3':
                a_format['vcodec'] = 'none'
            else:
                a_format.update({
                    'width': int_or_none(published_url.get('width')),
                    'height': int_or_none(published_url.get('height')),
                })
            formats.append(a_format)

        subtitles = {}
        for caption in video_data.get('captions', []):
            a_caption = {
                'url': caption['url'],
                'ext': 'tt' if caption.get('format') == 'SMPTE-TT' else None,
            }
            subtitles.setdefault(caption['language'], []).append(a_caption)
        subtitles = self._merge_subtitles(subtitles, hls_subs, vtt_subs)

        return {
            'id': video_id,
            'formats': formats,
            'title': video_data.get('def_title'),
            'description': video_data.get('def_description'),
            'tags': video_data.get('def_tags', '').split(','),
            'categories': video_data.get('categories'),
            'thumbnail': video_data.get('src_image_url') or video_data.get('thumbnail'),
            'timestamp': int_or_none(video_data.get(
                'ts_published') or video_data.get('ts_added')),
            'uploader': video_data.get('mcp_id'),
            'duration': int_or_none(video_data.get('duration')),
            'subtitles': subtitles,
        }
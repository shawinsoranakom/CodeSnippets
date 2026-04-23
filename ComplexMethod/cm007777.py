def _get_anvato_videos(self, access_key, video_id):
        video_data = self._get_video_json(access_key, video_id)

        formats = []
        for published_url in video_data['published_urls']:
            video_url = published_url['embed_url']
            media_format = published_url.get('format')
            ext = determine_ext(video_url)

            if ext == 'smil' or media_format == 'smil':
                formats.extend(self._extract_smil_formats(video_url, video_id))
                continue

            tbr = int_or_none(published_url.get('kbps'))
            a_format = {
                'url': video_url,
                'format_id': ('-'.join(filter(None, ['http', published_url.get('cdn_name')]))).lower(),
                'tbr': tbr if tbr != 0 else None,
            }

            if media_format == 'm3u8' and tbr is not None:
                a_format.update({
                    'format_id': '-'.join(filter(None, ['hls', compat_str(tbr)])),
                    'ext': 'mp4',
                })
            elif media_format == 'm3u8-variant' or ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
                continue
            elif ext == 'mp3' or media_format == 'mp3':
                a_format['vcodec'] = 'none'
            else:
                a_format.update({
                    'width': int_or_none(published_url.get('width')),
                    'height': int_or_none(published_url.get('height')),
                })
            formats.append(a_format)

        self._sort_formats(formats)

        subtitles = {}
        for caption in video_data.get('captions', []):
            a_caption = {
                'url': caption['url'],
                'ext': 'tt' if caption.get('format') == 'SMPTE-TT' else None
            }
            subtitles.setdefault(caption['language'], []).append(a_caption)

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
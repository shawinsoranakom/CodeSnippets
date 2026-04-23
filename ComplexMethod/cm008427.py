def _real_extract(self, url):
        video_id = self._match_id(url)
        metadata = self._download_json(self._API_URL + video_id, video_id)

        formats = []
        for source_type, source in metadata['streams'].items():
            if source_type == 'smooth_Streaming':
                formats.extend(self._extract_ism_formats(source['url'], video_id, 'mss', fatal=False))
            elif source_type == 'apple_HTTP_Live_Streaming':
                formats.extend(self._extract_m3u8_formats(source['url'], video_id, 'mp4', fatal=False))
            elif source_type == 'mPEG_DASH':
                formats.extend(self._extract_mpd_formats(source['url'], video_id, fatal=False))
            else:
                formats.append({
                    'format_id': source_type,
                    'url': source['url'],
                    'height': source.get('heightPixels'),
                    'width': source.get('widthPixels'),
                })

        subtitles = {
            lang: [{
                'url': data.get('url'),
                'ext': 'vtt',
            }] for lang, data in traverse_obj(metadata, 'captions', default={}).items()
        }

        thumbnails = [{
            'url': thumb.get('url'),
            'width': thumb.get('width') or None,
            'height': thumb.get('height') or None,
        } for thumb in traverse_obj(metadata, ('snippet', 'thumbnails', ...))]
        self._remove_duplicate_formats(thumbnails)

        return {
            'id': video_id,
            'title': traverse_obj(metadata, ('snippet', 'title')),
            'timestamp': unified_timestamp(traverse_obj(metadata, ('snippet', 'activeStartDate'))),
            'age_limit': int_or_none(traverse_obj(metadata, ('snippet', 'minimumAge'))) or 0,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
        }
def _extract_video(self, video, team, extract_all=True):
        video_id = str(video['nid'])
        team = video['brand']

        info = {
            'id': video_id,
            'title': video.get('title') or video.get('headline') or video['shortHeadline'],
            'description': video.get('description'),
            'timestamp': parse_iso8601(video.get('published')),
        }

        subtitles = {}
        captions = try_get(video, lambda x: x['videoCaptions']['sidecars'], dict) or {}
        for caption_url in captions.values():
            subtitles.setdefault('en', []).append({'url': caption_url})

        formats = []
        mp4_url = video.get('mp4')
        if mp4_url:
            formats.append({
                'url': mp4_url,
            })

        if extract_all:
            source_url = video.get('videoSource')
            if source_url and not source_url.startswith('s3://') and self._is_valid_url(source_url, video_id, 'source'):
                formats.append({
                    'format_id': 'source',
                    'url': source_url,
                    'quality': 1,
                })

            m3u8_url = video.get('m3u8')
            if m3u8_url:
                if '.akamaihd.net/i/' in m3u8_url:
                    formats.extend(self._extract_akamai_formats(
                        m3u8_url, video_id, {'http': 'pmd.cdn.turner.com'}))
                else:
                    formats.extend(self._extract_m3u8_formats(
                        m3u8_url, video_id, 'mp4',
                        'm3u8_native', m3u8_id='hls', fatal=False))

            content_xml = video.get('contentXml')
            if team and content_xml:
                cvp_info = self._extract_nba_cvp_info(
                    team + content_xml, video_id, fatal=False)
                if cvp_info:
                    formats.extend(cvp_info['formats'])
                    subtitles = self._merge_subtitles(subtitles, cvp_info['subtitles'])
                    info = merge_dicts(info, cvp_info)

        else:
            info.update(self._embed_url_result(team, video['videoId']))

        info.update({
            'formats': formats,
            'subtitles': subtitles,
        })

        return info
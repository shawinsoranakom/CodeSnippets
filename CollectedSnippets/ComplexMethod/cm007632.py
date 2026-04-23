def _real_extract(self, url):
        video_id = self._match_id(url)

        video_data = self._download_json(
            # https://api.mais.uol.com.br/apiuol/v4/player/data/[MEDIA_ID]
            'https://api.mais.uol.com.br/apiuol/v3/media/detail/' + video_id,
            video_id)['item']
        media_id = compat_str(video_data['mediaId'])
        title = video_data['title']
        ver = video_data.get('revision', 2)

        uol_formats = self._download_json(
            'https://croupier.mais.uol.com.br/v3/formats/%s/jsonp' % media_id,
            media_id)
        quality = qualities(['mobile', 'WEBM', '360p', '720p', '1080p'])
        formats = []
        for format_id, f in uol_formats.items():
            if not isinstance(f, dict):
                continue
            f_url = f.get('url') or f.get('secureUrl')
            if not f_url:
                continue
            query = {
                'ver': ver,
                'r': 'http://mais.uol.com.br',
            }
            for k in ('token', 'sign'):
                v = f.get(k)
                if v:
                    query[k] = v
            f_url = update_url_query(f_url, query)
            if format_id == 'HLS':
                m3u8_formats = self._extract_m3u8_formats(
                    f_url, media_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False)
                encoded_query = compat_urllib_parse_urlencode(query)
                for m3u8_f in m3u8_formats:
                    m3u8_f['extra_param_to_segment_url'] = encoded_query
                    m3u8_f['url'] = update_url_query(m3u8_f['url'], query)
                formats.extend(m3u8_formats)
                continue
            formats.append({
                'format_id': format_id,
                'url': f_url,
                'quality': quality(format_id),
                'preference': -1,
            })
        self._sort_formats(formats)

        tags = []
        for tag in video_data.get('tags', []):
            tag_description = tag.get('description')
            if not tag_description:
                continue
            tags.append(tag_description)

        thumbnails = []
        for q in ('Small', 'Medium', 'Wmedium', 'Large', 'Wlarge', 'Xlarge'):
            q_url = video_data.get('thumb' + q)
            if not q_url:
                continue
            thumbnails.append({
                'id': q,
                'url': q_url,
            })

        return {
            'id': media_id,
            'title': title,
            'description': clean_html(video_data.get('description')),
            'thumbnails': thumbnails,
            'duration': parse_duration(video_data.get('duration')),
            'tags': tags,
            'formats': formats,
            'timestamp': parse_iso8601(video_data.get('publishDate'), ' '),
            'view_count': int_or_none(video_data.get('viewsQtty')),
        }
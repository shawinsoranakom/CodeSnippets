def _extract_video(self, filter_key, filter_value):
        video = self._download_json(
            'https://neulionscnbav2-a.akamaihd.net/solr/nbad_program/usersearch',
            filter_value, query={
                'fl': 'description,image,name,pid,releaseDate,runtime,tags,seoName',
                'q': filter_key + ':' + filter_value,
                'wt': 'json',
            })['response']['docs'][0]

        video_id = str(video['pid'])
        title = video['name']

        formats = []
        m3u8_url = (self._download_json(
            'https://watch.nba.com/service/publishpoint', video_id, query={
                'type': 'video',
                'format': 'json',
                'id': video_id,
            }, headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0_1 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A402 Safari/604.1',
            }, fatal=False) or {}).get('path')
        if m3u8_url:
            m3u8_formats = self._extract_m3u8_formats(
                re.sub(r'_(?:pc|iphone)\.', '.', m3u8_url), video_id, 'mp4',
                'm3u8_native', m3u8_id='hls', fatal=False)
            formats.extend(m3u8_formats)
            for f in m3u8_formats:
                http_f = f.copy()
                http_f.update({
                    'format_id': http_f['format_id'].replace('hls-', 'http-'),
                    'protocol': 'http',
                    'url': http_f['url'].replace('.m3u8', ''),
                })
                formats.append(http_f)

        info = {
            'id': video_id,
            'title': title,
            'thumbnail': urljoin('https://nbadsdmt.akamaized.net/media/nba/nba/thumbs/', video.get('image')),
            'description': video.get('description'),
            'duration': int_or_none(video.get('runtime')),
            'timestamp': parse_iso8601(video.get('releaseDate')),
            'tags': video.get('tags'),
        }

        seo_name = video.get('seoName')
        if seo_name and re.search(r'\d{4}/\d{2}/\d{2}/', seo_name):
            base_path = ''
            if seo_name.startswith('teams/'):
                base_path += seo_name.split('/')[1] + '/'
            base_path += 'video/'
            cvp_info = self._extract_nba_cvp_info(
                base_path + seo_name + '.xml', video_id, False)
            if cvp_info:
                formats.extend(cvp_info['formats'])
                info = merge_dicts(info, cvp_info)

        info['formats'] = formats
        return info
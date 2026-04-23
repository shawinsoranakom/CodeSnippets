def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        qs = compat_parse_qs(re.match(self._VALID_URL, url).group('qs'))
        if not qs.get('filename') or not qs.get('type') or not qs.get('comm'):
            raise ExtractorError('Invalid URL', expected=True)

        video_id = re.sub(r'.mp4$', '', qs['filename'][0])

        webpage = self._download_webpage(url, video_id)

        if smuggled_data.get('force_title'):
            title = smuggled_data['force_title']
        else:
            title = self._html_search_regex(r'<title>([^<]+)</title>', webpage, video_id)
        poster = qs.get('poster')
        thumbnail = poster[0] if poster else None

        video_type = qs['type'][0]
        committee = video_type if video_type == 'arch' else qs['comm'][0]
        stream_num, domain = self._get_info_for_comm(committee)

        formats = []
        if video_type == 'arch':
            filename = video_id if '.' in video_id else video_id + '.mp4'
            formats = [{
                # All parameters in the query string are necessary to prevent a 403 error
                'url': compat_urlparse.urljoin(domain, filename) + '?v=3.1.0&fp=&r=&g=',
            }]
        else:
            hdcore_sign = 'hdcore=3.1.0'
            url_params = (domain, video_id, stream_num)
            f4m_url = '%s/z/%s_1@%s/manifest.f4m?' % url_params + hdcore_sign
            m3u8_url = '%s/i/%s_1@%s/master.m3u8' % url_params
            for entry in self._extract_f4m_formats(f4m_url, video_id, f4m_id='f4m'):
                # URLs without the extra param induce an 404 error
                entry.update({'extra_param_to_segment_url': hdcore_sign})
                formats.append(entry)
            for entry in self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4', m3u8_id='m3u8'):
                mobj = re.search(r'(?P<tag>(?:-p|-b)).m3u8', entry['url'])
                if mobj:
                    entry['format_id'] += mobj.group('tag')
                formats.append(entry)

            self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
        }
def _real_extract(self, url):
        show_id, season_id, video_id = re.match(self._VALID_URL, url).groups()

        response = self._download_info(
            show_id, 'season/%s' % season_id,
            video_id, query={'video_id': video_id})

        vid = int(video_id)
        video_data = list(filter(
            lambda episode: episode.get('video_id') == vid, response))[0]
        title = video_data['title']
        formats = []

        # vvvvid embed_info decryption algorithm is reverse engineered from function $ds(h) at vvvvid.js
        def ds(h):
            g = "MNOPIJKL89+/4567UVWXQRSTEFGHABCDcdefYZabstuvopqr0123wxyzklmnghij"

            def f(m):
                l = []
                o = 0
                b = False
                m_len = len(m)
                while ((not b) and o < m_len):
                    n = m[o] << 2
                    o += 1
                    k = -1
                    j = -1
                    if o < m_len:
                        n += m[o] >> 4
                        o += 1
                        if o < m_len:
                            k = (m[o - 1] << 4) & 255
                            k += m[o] >> 2
                            o += 1
                            if o < m_len:
                                j = (m[o - 1] << 6) & 255
                                j += m[o]
                                o += 1
                            else:
                                b = True
                        else:
                            b = True
                    else:
                        b = True
                    l.append(n)
                    if k != -1:
                        l.append(k)
                    if j != -1:
                        l.append(j)
                return l

            c = []
            for e in h:
                c.append(g.index(e))

            c_len = len(c)
            for e in range(c_len * 2 - 1, -1, -1):
                a = c[e % c_len] ^ c[(e + 1) % c_len]
                c[e % c_len] = a

            c = f(c)
            d = ''
            for e in c:
                d += chr(e)

            return d

        info = {}

        def metadata_from_url(r_url):
            if not info and r_url:
                mobj = re.search(r'_(?:S(\d+))?Ep(\d+)', r_url)
                if mobj:
                    info['episode_number'] = int(mobj.group(2))
                    season_number = mobj.group(1)
                    if season_number:
                        info['season_number'] = int(season_number)

        video_type = video_data.get('video_type')
        is_youtube = False
        for quality in ('', '_sd'):
            embed_code = video_data.get('embed_info' + quality)
            if not embed_code:
                continue
            embed_code = ds(embed_code)
            if video_type == 'video/kenc':
                embed_code = re.sub(r'https?(://[^/]+)/z/', r'https\1/i/', embed_code).replace('/manifest.f4m', '/master.m3u8')
                kenc = self._download_json(
                    'https://www.vvvvid.it/kenc', video_id, query={
                        'action': 'kt',
                        'conn_id': self._conn_id,
                        'url': embed_code,
                    }, fatal=False) or {}
                kenc_message = kenc.get('message')
                if kenc_message:
                    embed_code += '?' + ds(kenc_message)
                formats.extend(self._extract_m3u8_formats(
                    embed_code, video_id, 'mp4', m3u8_id='hls', fatal=False))
            elif video_type == 'video/rcs':
                formats.extend(self._extract_akamai_formats(embed_code, video_id))
            elif video_type == 'video/youtube':
                info.update({
                    '_type': 'url_transparent',
                    'ie_key': YoutubeIE.ie_key(),
                    'url': embed_code,
                })
                is_youtube = True
                break
            elif video_type == 'video/dash':
                formats.extend(self._extract_m3u8_formats(
                    embed_code, video_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                formats.extend(self._extract_wowza_formats(
                    'http://sb.top-ix.org/videomg/_definst_/mp4:%s/playlist.m3u8' % embed_code, video_id))
            metadata_from_url(embed_code)

        if not is_youtube:
            self._sort_formats(formats)
            info['formats'] = formats

        metadata_from_url(video_data.get('thumbnail'))
        info.update(self._extract_common_video_info(video_data))
        info.update({
            'id': video_id,
            'title': title,
            'duration': int_or_none(video_data.get('length')),
            'series': video_data.get('show_title'),
            'season_id': season_id,
            'episode': title,
            'view_count': int_or_none(video_data.get('views')),
            'like_count': int_or_none(video_data.get('video_likes')),
            'repost_count': int_or_none(video_data.get('video_shares')),
        })
        return info
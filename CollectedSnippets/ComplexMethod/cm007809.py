def _extract_rss(self, url, video_id, doc):
        playlist_title = doc.find('./channel/title').text
        playlist_desc_el = doc.find('./channel/description')
        playlist_desc = None if playlist_desc_el is None else playlist_desc_el.text

        NS_MAP = {
            'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        }

        entries = []
        for it in doc.findall('./channel/item'):
            next_url = None
            enclosure_nodes = it.findall('./enclosure')
            for e in enclosure_nodes:
                next_url = e.attrib.get('url')
                if next_url:
                    break

            if not next_url:
                next_url = xpath_text(it, 'link', fatal=False)

            if not next_url:
                continue

            def itunes(key):
                return xpath_text(
                    it, xpath_with_ns('./itunes:%s' % key, NS_MAP),
                    default=None)

            duration = itunes('duration')
            explicit = (itunes('explicit') or '').lower()
            if explicit in ('true', 'yes'):
                age_limit = 18
            elif explicit in ('false', 'no'):
                age_limit = 0
            else:
                age_limit = None

            entries.append({
                '_type': 'url_transparent',
                'url': next_url,
                'title': it.find('title').text,
                'description': xpath_text(it, 'description', default=None),
                'timestamp': unified_timestamp(
                    xpath_text(it, 'pubDate', default=None)),
                'duration': int_or_none(duration) or parse_duration(duration),
                'thumbnail': url_or_none(xpath_attr(it, xpath_with_ns('./itunes:image', NS_MAP), 'href')),
                'episode': itunes('title'),
                'episode_number': int_or_none(itunes('episode')),
                'season_number': int_or_none(itunes('season')),
                'age_limit': age_limit,
            })

        return {
            '_type': 'playlist',
            'id': url,
            'title': playlist_title,
            'description': playlist_desc,
            'entries': entries,
        }
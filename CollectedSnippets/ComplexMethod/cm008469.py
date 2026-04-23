def extract_addr(addr, add_meta={}):
            parsed_meta, res = self._parse_url_key(addr.get('url_key', ''))
            is_bytevc2 = parsed_meta.get('vcodec') == 'bytevc2'
            if res:
                known_resolutions.setdefault(res, {}).setdefault('height', int_or_none(addr.get('height')))
                known_resolutions[res].setdefault('width', int_or_none(addr.get('width')))
                parsed_meta.update(known_resolutions.get(res, {}))
                add_meta.setdefault('height', int_or_none(res[:-1]))
            return [{
                'url': url,
                'filesize': int_or_none(addr.get('data_size')),
                'ext': 'mp4',
                'acodec': 'aac',
                'source_preference': -2 if 'aweme/v1' in url else -1,  # Downloads from API might get blocked
                **add_meta, **parsed_meta,
                # bytevc2 is bytedance's own custom h266/vvc codec, as-of-yet unplayable
                'preference': -100 if is_bytevc2 else -1,
                'format_note': join_nonempty(
                    add_meta.get('format_note'), '(API)' if 'aweme/v1' in url else None,
                    '(UNPLAYABLE)' if is_bytevc2 else None, delim=' '),
                **audio_meta(url),
            } for url in addr.get('url_list') or []]
def _parse_html5_media_entries(self, base_url, webpage, video_id, m3u8_id=None, m3u8_entry_protocol='m3u8', mpd_id=None, preference=None):
        def absolute_url(item_url):
            return urljoin(base_url, item_url)

        def parse_content_type(content_type):
            if not content_type:
                return {}
            ctr = re.search(r'(?P<mimetype>[^/]+/[^;]+)(?:;\s*codecs="?(?P<codecs>[^"]+))?', content_type)
            if ctr:
                mimetype, codecs = ctr.groups()
                f = parse_codecs(codecs)
                f['ext'] = mimetype2ext(mimetype)
                return f
            return {}

        def _media_formats(src, cur_media_type, type_info=None):
            type_info = type_info or {}
            full_url = absolute_url(src)
            ext = type_info.get('ext') or determine_ext(full_url)
            if ext == 'm3u8':
                is_plain_url = False
                formats = self._extract_m3u8_formats(
                    full_url, video_id, ext='mp4',
                    entry_protocol=m3u8_entry_protocol, m3u8_id=m3u8_id,
                    preference=preference, fatal=False)
            elif ext == 'mpd':
                is_plain_url = False
                formats = self._extract_mpd_formats(
                    full_url, video_id, mpd_id=mpd_id, fatal=False)
            else:
                is_plain_url = True
                formats = [{
                    'url': full_url,
                    'vcodec': 'none' if cur_media_type == 'audio' else None,
                    'ext': ext,
                }]
            return is_plain_url, formats

        entries = []
        # amp-video and amp-audio are very similar to their HTML5 counterparts
        # so we wll include them right here (see
        # https://www.ampproject.org/docs/reference/components/amp-video)
        # For dl8-* tags see https://delight-vr.com/documentation/dl8-video/
        _MEDIA_TAG_NAME_RE = r'(?:(?:amp|dl8(?:-live)?)-)?(video(?:-js)?|audio)'
        media_tags = [(media_tag, media_tag_name, media_type, '')
                      for media_tag, media_tag_name, media_type
                      in re.findall(r'(?s)(<(%s)[^>]*/>)' % _MEDIA_TAG_NAME_RE, webpage)]
        media_tags.extend(re.findall(
            # We only allow video|audio followed by a whitespace or '>'.
            # Allowing more characters may end up in significant slow down (see
            # https://github.com/ytdl-org/youtube-dl/issues/11979, example URL:
            # http://www.porntrex.com/maps/videositemap.xml).
            r'(?s)(<(?P<tag>%s)(?:\s+[^>]*)?>)(.*?)</(?P=tag)>' % _MEDIA_TAG_NAME_RE, webpage))
        for media_tag, _, media_type, media_content in media_tags:
            media_info = {
                'formats': [],
                'subtitles': {},
            }
            media_attributes = extract_attributes(media_tag)
            src = strip_or_none(media_attributes.get('src'))
            if src:
                f = parse_content_type(media_attributes.get('type'))
                _, formats = _media_formats(src, media_type, f)
                media_info['formats'].extend(formats)
            media_info['thumbnail'] = absolute_url(media_attributes.get('poster'))
            if media_content:
                for source_tag in re.findall(r'<source[^>]+>', media_content):
                    s_attr = extract_attributes(source_tag)
                    # data-video-src and data-src are non standard but seen
                    # several times in the wild
                    src = strip_or_none(dict_get(s_attr, ('src', 'data-video-src', 'data-src')))
                    if not src:
                        continue
                    f = parse_content_type(s_attr.get('type'))
                    is_plain_url, formats = _media_formats(src, media_type, f)
                    if is_plain_url:
                        # width, height, res, label and title attributes are
                        # all not standard but seen several times in the wild
                        labels = [
                            s_attr.get(lbl)
                            for lbl in ('label', 'title')
                            if str_or_none(s_attr.get(lbl))
                        ]
                        width = int_or_none(s_attr.get('width'))
                        height = (int_or_none(s_attr.get('height'))
                                  or int_or_none(s_attr.get('res')))
                        if not width or not height:
                            for lbl in labels:
                                resolution = parse_resolution(lbl)
                                if not resolution:
                                    continue
                                width = width or resolution.get('width')
                                height = height or resolution.get('height')
                        for lbl in labels:
                            tbr = parse_bitrate(lbl)
                            if tbr:
                                break
                        else:
                            tbr = None
                        f.update({
                            'width': width,
                            'height': height,
                            'tbr': tbr,
                            'format_id': s_attr.get('label') or s_attr.get('title'),
                        })
                        f.update(formats[0])
                        media_info['formats'].append(f)
                    else:
                        media_info['formats'].extend(formats)
                for track_tag in re.findall(r'<track[^>]+>', media_content):
                    track_attributes = extract_attributes(track_tag)
                    kind = track_attributes.get('kind')
                    if not kind or kind in ('subtitles', 'captions'):
                        src = strip_or_none(track_attributes.get('src'))
                        if not src:
                            continue
                        lang = track_attributes.get('srclang') or track_attributes.get('lang') or track_attributes.get('label')
                        media_info['subtitles'].setdefault(lang, []).append({
                            'url': absolute_url(src),
                        })
            for f in media_info['formats']:
                f.setdefault('http_headers', {})['Referer'] = base_url
            if media_info['formats'] or media_info['subtitles']:
                entries.append(media_info)
        return entries
def extract_media(x_media_line):
            media = parse_m3u8_attributes(x_media_line)
            # As per [1, 4.3.4.1] TYPE, GROUP-ID and NAME are REQUIRED
            media_type, group_id, name = media.get('TYPE'), media.get('GROUP-ID'), media.get('NAME')
            if not (media_type and group_id and name):
                return
            groups.setdefault(group_id, []).append(media)
            # <https://tools.ietf.org/html/rfc8216#section-4.3.4.1>
            if media_type == 'SUBTITLES':
                # According to RFC 8216 §4.3.4.2.1, URI is REQUIRED in the
                # EXT-X-MEDIA tag if the media type is SUBTITLES.
                # However, lack of URI has been spotted in the wild.
                # e.g. NebulaIE; see https://github.com/yt-dlp/yt-dlp/issues/339
                if not media.get('URI'):
                    return
                url = format_url(media['URI'])
                sub_info = {
                    'url': url,
                    'ext': determine_ext(url),
                }
                if sub_info['ext'] == 'm3u8':
                    # Per RFC 8216 §3.1, the only possible subtitle format m3u8
                    # files may contain is WebVTT:
                    # <https://tools.ietf.org/html/rfc8216#section-3.1>
                    sub_info['ext'] = 'vtt'
                    sub_info['protocol'] = 'm3u8_native'
                lang = media.get('LANGUAGE') or 'und'
                subtitles.setdefault(lang, []).append(sub_info)
            if media_type not in ('VIDEO', 'AUDIO'):
                return
            media_url = media.get('URI')
            if media_url:
                manifest_url = format_url(media_url)
                is_audio = media_type == 'AUDIO'
                is_alternate = media.get('DEFAULT') == 'NO' or media.get('AUTOSELECT') == 'NO'
                formats.extend({
                    'format_id': join_nonempty(m3u8_id, group_id, name, idx),
                    'format_note': name,
                    'format_index': idx,
                    'url': manifest_url,
                    'manifest_url': m3u8_url,
                    'language': media.get('LANGUAGE'),
                    'ext': ext,
                    'protocol': entry_protocol,
                    'preference': preference,
                    'quality': quality,
                    'has_drm': has_drm,
                    'vcodec': 'none' if is_audio else None,
                    # Alternate audio formats (e.g. audio description) should be deprioritized
                    'source_preference': -2 if is_audio and is_alternate else None,
                    # Save this to assign source_preference based on associated video stream
                    '_audio_group_id': group_id if is_audio and not is_alternate else None,
                } for idx in _extract_m3u8_playlist_indices(manifest_url))
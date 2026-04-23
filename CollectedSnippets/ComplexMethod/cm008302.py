def process_format_list(format_list, format_id=''):
            nonlocal formats, has_drm
            if not isinstance(format_list, list):
                format_list = [format_list]
            for format_dict in format_list:
                if not isinstance(format_dict, dict):
                    continue
                if (not self.get_param('allow_unplayable_formats')
                        and traverse_obj(format_dict, ('drm', 'keySystem'))):
                    has_drm = True
                    continue
                format_url = url_or_none(format_dict.get('src'))
                format_type = format_dict.get('type')
                ext = determine_ext(format_url)
                if (format_type == 'application/x-mpegURL'
                        or format_id == 'HLS' or ext == 'm3u8'):
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls',
                        fatal=False))
                elif (format_type == 'application/dash+xml'
                      or format_id == 'DASH' or ext == 'mpd'):
                    formats.extend(self._extract_mpd_formats(
                        format_url, video_id, mpd_id='dash', fatal=False))
                else:
                    formats.append({
                        'url': format_url,
                    })
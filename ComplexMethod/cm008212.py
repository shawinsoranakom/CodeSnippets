def _extract_from_api(self, video_id, unlisted_hash=None):
        for retry in (False, True):
            try:
                video = self._call_videos_api(video_id, unlisted_hash)
                break
            except ExtractorError as e:
                if not isinstance(e.cause, HTTPError):
                    raise
                response = traverse_obj(
                    self._webpage_read_content(e.cause.response, e.cause.response.url, video_id, fatal=False),
                    ({json.loads}, {dict})) or {}
                if (
                    not retry and e.cause.status == 400
                    and 'password' in traverse_obj(response, ('invalid_parameters', ..., 'field'))
                ):
                    self._verify_video_password(video_id)
                elif e.cause.status == 404 and response.get('error_code') == 5460:
                    self.raise_login_required(join_nonempty(
                        traverse_obj(response, ('error', {str.strip})),
                        'Authentication may be needed due to your location.',
                        'If your IP address is located in Europe you could try using a VPN/proxy,',
                        f'or else u{self._login_hint()[1:]}',
                        delim=' '), method=None)
                else:
                    raise

        if config_url := traverse_obj(video, ('config_url', {url_or_none})):
            info = self._parse_config(self._download_json(config_url, video_id), video_id)
        else:
            info = self._parse_api_response(video, video_id, unlisted_hash)

        source_format = self._extract_original_format(
            f'https://vimeo.com/{video_id}', video_id, unlisted_hash)
        if source_format:
            info['formats'].append(source_format)

        get_timestamp = lambda x: parse_iso8601(video.get(x + '_time'))
        info.update({
            'description': video.get('description'),
            'license': video.get('license'),
            'release_timestamp': get_timestamp('release'),
            'timestamp': get_timestamp('created'),
            'view_count': int_or_none(try_get(video, lambda x: x['stats']['plays'])),
        })
        connections = try_get(
            video, lambda x: x['metadata']['connections'], dict) or {}
        for k in ('comment', 'like'):
            info[k + '_count'] = int_or_none(try_get(connections, lambda x: x[k + 's']['total']))
        return info
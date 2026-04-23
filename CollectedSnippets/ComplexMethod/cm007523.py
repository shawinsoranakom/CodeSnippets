def _parse_stream(self, stream, url):
        stream_value = stream.get('value') or {}
        stream_type = stream_value.get('stream_type')
        source = stream_value.get('source') or {}
        media = stream_value.get(stream_type) or {}
        signing_channel = stream.get('signing_channel') or {}
        channel_name = signing_channel.get('name')
        channel_claim_id = signing_channel.get('claim_id')
        channel_url = None
        if channel_name and channel_claim_id:
            channel_url = self._permanent_url(url, channel_name, channel_claim_id)

        info = {
            'thumbnail': try_get(stream_value, lambda x: x['thumbnail']['url'], compat_str),
            'description': stream_value.get('description'),
            'license': stream_value.get('license'),
            'timestamp': int_or_none(stream.get('timestamp')),
            'release_timestamp': int_or_none(stream_value.get('release_time')),
            'tags': stream_value.get('tags'),
            'duration': int_or_none(media.get('duration')),
            'channel': try_get(signing_channel, lambda x: x['value']['title']),
            'channel_id': channel_claim_id,
            'channel_url': channel_url,
            'ext': determine_ext(source.get('name')) or mimetype2ext(source.get('media_type')),
            'filesize': int_or_none(source.get('size')),
        }
        if stream_type == 'audio':
            info['vcodec'] = 'none'
        else:
            info.update({
                'width': int_or_none(media.get('width')),
                'height': int_or_none(media.get('height')),
            })
        return info
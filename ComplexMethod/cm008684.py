def _extract_product_media(self, product_media):
        media_id = product_media.get('code') or _pk_to_id(product_media.get('pk'))
        vcodec = product_media.get('video_codec')
        dash_manifest_raw = product_media.get('video_dash_manifest')
        videos_list = product_media.get('video_versions')
        if not (dash_manifest_raw or videos_list):
            return {}

        formats = [{
            'format_id': fmt.get('id'),
            'url': fmt.get('url'),
            'width': fmt.get('width'),
            'height': fmt.get('height'),
            'vcodec': vcodec,
        } for fmt in videos_list or []]
        if dash_manifest_raw:
            formats.extend(self._parse_mpd_formats(self._parse_xml(dash_manifest_raw, media_id), mpd_id='dash'))

        thumbnails = [{
            'url': thumbnail.get('url'),
            'width': thumbnail.get('width'),
            'height': thumbnail.get('height'),
        } for thumbnail in traverse_obj(product_media, ('image_versions2', 'candidates')) or []]
        return {
            'id': media_id,
            'duration': float_or_none(product_media.get('video_duration')),
            'formats': formats,
            'thumbnails': thumbnails,
        }
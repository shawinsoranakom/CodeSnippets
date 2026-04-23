def _extract_video(self, data, extract_formats=True):
        video_id = data['id']

        title = (data.get('title') or data.get('grid_title') or video_id).strip()

        urls = []
        formats = []
        duration = None
        if extract_formats:
            for format_id, format_dict in data['videos']['video_list'].items():
                if not isinstance(format_dict, dict):
                    continue
                format_url = url_or_none(format_dict.get('url'))
                if not format_url or format_url in urls:
                    continue
                urls.append(format_url)
                duration = float_or_none(format_dict.get('duration'), scale=1000)
                ext = determine_ext(format_url)
                if 'hls' in format_id.lower() or ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id=format_id, fatal=False))
                else:
                    formats.append({
                        'url': format_url,
                        'format_id': format_id,
                        'width': int_or_none(format_dict.get('width')),
                        'height': int_or_none(format_dict.get('height')),
                        'duration': duration,
                    })
            self._sort_formats(
                formats, field_preference=('height', 'width', 'tbr', 'format_id'))

        description = data.get('description') or data.get('description_html') or data.get('seo_description')
        timestamp = unified_timestamp(data.get('created_at'))

        def _u(field):
            return try_get(data, lambda x: x['closeup_attribution'][field], compat_str)

        uploader = _u('full_name')
        uploader_id = _u('id')

        repost_count = int_or_none(data.get('repin_count'))
        comment_count = int_or_none(data.get('comment_count'))
        categories = try_get(data, lambda x: x['pin_join']['visual_annotation'], list)
        tags = data.get('hashtags')

        thumbnails = []
        images = data.get('images')
        if isinstance(images, dict):
            for thumbnail_id, thumbnail in images.items():
                if not isinstance(thumbnail, dict):
                    continue
                thumbnail_url = url_or_none(thumbnail.get('url'))
                if not thumbnail_url:
                    continue
                thumbnails.append({
                    'url': thumbnail_url,
                    'width': int_or_none(thumbnail.get('width')),
                    'height': int_or_none(thumbnail.get('height')),
                })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'thumbnails': thumbnails,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'repost_count': repost_count,
            'comment_count': comment_count,
            'categories': categories,
            'tags': tags,
            'formats': formats,
            'extractor_key': PinterestIE.ie_key(),
        }
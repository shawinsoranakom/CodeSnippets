def _extract_video(self, data, extract_formats=True):
        video_id = data['id']
        thumbnails = []
        images = data.get('images')
        if isinstance(images, dict):
            for thumbnail in images.values():
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

        info = {
            'title': strip_or_none(traverse_obj(data, 'title', 'grid_title', default='')),
            'description': traverse_obj(data, 'seo_description', 'description'),
            'timestamp': unified_timestamp(data.get('created_at')),
            'thumbnails': thumbnails,
            'uploader': traverse_obj(data, ('closeup_attribution', 'full_name')),
            'uploader_id': str_or_none(traverse_obj(data, ('closeup_attribution', 'id'))),
            'repost_count': int_or_none(data.get('repin_count')),
            'comment_count': int_or_none(data.get('comment_count')),
            'categories': traverse_obj(data, ('pin_join', 'visual_annotation'), expected_type=list),
            'tags': traverse_obj(data, 'hashtags', expected_type=list),
        }

        urls = []
        formats = []
        duration = None
        domain = data.get('domain', '')
        if domain.lower() != 'uploaded by user' and traverse_obj(data, ('embed', 'src')):
            if not info['title']:
                info['title'] = None
            return {
                '_type': 'url_transparent',
                'url': data['embed']['src'],
                **info,
            }

        elif extract_formats:
            video_list = traverse_obj(
                data, ('videos', 'video_list'),
                ('story_pin_data', 'pages', ..., 'blocks', ..., 'video', 'video_list'),
                expected_type=dict, get_all=False, default={})
            for format_id, format_dict in video_list.items():
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

        return {
            'id': video_id,
            'formats': formats,
            'duration': duration,
            'webpage_url': f'https://www.pinterest.com/pin/{video_id}/',
            'extractor_key': PinterestIE.ie_key(),
            'extractor': PinterestIE.IE_NAME,
            **info,
        }
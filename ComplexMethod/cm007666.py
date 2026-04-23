def entries():
            featured_video = story.get('featuredVideo') or {}
            feed = try_get(featured_video, lambda x: x['video']['feed'])
            if feed:
                yield {
                    '_type': 'url',
                    'id': featured_video.get('id'),
                    'title': featured_video.get('name'),
                    'url': feed,
                    'thumbnail': featured_video.get('images'),
                    'description': featured_video.get('description'),
                    'timestamp': parse_iso8601(featured_video.get('uploadDate')),
                    'duration': parse_duration(featured_video.get('duration')),
                    'ie_key': AbcNewsVideoIE.ie_key(),
                }

            for inline in (article_contents.get('inlines') or []):
                inline_type = inline.get('type')
                if inline_type == 'iframe':
                    iframe_url = try_get(inline, lambda x: x['attrs']['src'])
                    if iframe_url:
                        yield self.url_result(iframe_url)
                elif inline_type == 'video':
                    video_id = inline.get('id')
                    if video_id:
                        yield {
                            '_type': 'url',
                            'id': video_id,
                            'url': 'http://abcnews.go.com/video/embed?id=' + video_id,
                            'thumbnail': inline.get('imgSrc') or inline.get('imgDefault'),
                            'description': inline.get('description'),
                            'duration': parse_duration(inline.get('duration')),
                            'ie_key': AbcNewsVideoIE.ie_key(),
                        }
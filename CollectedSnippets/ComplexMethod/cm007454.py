def _real_extract(self, url):
        video_id = self._match_id(url)
        post = self._download_json(
            'https://www.patreon.com/api/posts/' + video_id, video_id, query={
                'fields[media]': 'download_url,mimetype,size_bytes',
                'fields[post]': 'comment_count,content,embed,image,like_count,post_file,published_at,title',
                'fields[user]': 'full_name,url',
                'json-api-use-default-includes': 'false',
                'include': 'media,user',
            })
        attributes = post['data']['attributes']
        title = attributes['title'].strip()
        image = attributes.get('image') or {}
        info = {
            'id': video_id,
            'title': title,
            'description': clean_html(attributes.get('content')),
            'thumbnail': image.get('large_url') or image.get('url'),
            'timestamp': parse_iso8601(attributes.get('published_at')),
            'like_count': int_or_none(attributes.get('like_count')),
            'comment_count': int_or_none(attributes.get('comment_count')),
        }

        for i in post.get('included', []):
            i_type = i.get('type')
            if i_type == 'media':
                media_attributes = i.get('attributes') or {}
                download_url = media_attributes.get('download_url')
                ext = mimetype2ext(media_attributes.get('mimetype'))
                if download_url and ext in KNOWN_EXTENSIONS:
                    info.update({
                        'ext': ext,
                        'filesize': int_or_none(media_attributes.get('size_bytes')),
                        'url': download_url,
                    })
            elif i_type == 'user':
                user_attributes = i.get('attributes')
                if user_attributes:
                    info.update({
                        'uploader': user_attributes.get('full_name'),
                        'uploader_id': str_or_none(i.get('id')),
                        'uploader_url': user_attributes.get('url'),
                    })

        if not info.get('url'):
            embed_url = try_get(attributes, lambda x: x['embed']['url'])
            if embed_url:
                info.update({
                    '_type': 'url',
                    'url': embed_url,
                })

        if not info.get('url'):
            post_file = attributes['post_file']
            ext = determine_ext(post_file.get('name'))
            if ext in KNOWN_EXTENSIONS:
                info.update({
                    'ext': ext,
                    'url': post_file['url'],
                })

        return info
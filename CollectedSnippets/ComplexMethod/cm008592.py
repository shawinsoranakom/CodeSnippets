def _real_extract(self, url):
        post_id = self._match_id(url)
        post = self._download_json(
            'https://9gag.com/v1/post', post_id, query={
                'id': post_id,
            }, impersonate=True)['data']['post']

        if post.get('type') != 'Animated':
            self.raise_no_formats(
                'The given url does not contain a video',
                expected=True)

        duration = None
        formats = []
        thumbnails = []
        for key, image in (post.get('images') or {}).items():
            image_url = url_or_none(image.get('url'))
            if not image_url:
                continue
            ext = determine_ext(image_url)
            image_id = key.strip('image')
            common = {
                'url': image_url,
                'width': int_or_none(image.get('width')),
                'height': int_or_none(image.get('height')),
            }
            if ext in ('jpg', 'png'):
                webp_url = image.get('webpUrl')
                if webp_url:
                    t = common.copy()
                    t.update({
                        'id': image_id + '-webp',
                        'url': webp_url,
                    })
                    thumbnails.append(t)
                common.update({
                    'id': image_id,
                    'ext': ext,
                })
                thumbnails.append(common)
            elif ext in ('webm', 'mp4'):
                if not duration:
                    duration = int_or_none(image.get('duration'))
                common['acodec'] = 'none' if image.get('hasAudio') == 0 else None
                for vcodec in ('vp8', 'vp9', 'h265'):
                    c_url = image.get(vcodec + 'Url')
                    if not c_url:
                        continue
                    c_f = common.copy()
                    c_f.update({
                        'format_id': image_id + '-' + vcodec,
                        'url': c_url,
                        'vcodec': vcodec,
                    })
                    formats.append(c_f)
                common.update({
                    'ext': ext,
                    'format_id': image_id,
                })
                formats.append(common)

        section = traverse_obj(post, ('postSection', 'name'))

        tags = None
        post_tags = post.get('tags')
        if post_tags:
            tags = []
            for tag in post_tags:
                tag_key = tag.get('key')
                if not tag_key:
                    continue
                tags.append(tag_key)

        return {
            'id': post_id,
            'title': unescapeHTML(post.get('title')),
            'timestamp': int_or_none(post.get('creationTs')),
            'duration': duration,
            'uploader': traverse_obj(post, ('creator', 'fullName')),
            'uploader_id': traverse_obj(post, ('creator', 'username')),
            'uploader_url': url_or_none(traverse_obj(post, ('creator', 'profileUrl'))),
            'formats': formats,
            'thumbnails': thumbnails,
            'like_count': int_or_none(post.get('upVoteCount')),
            'dislike_count': int_or_none(post.get('downVoteCount')),
            'comment_count': int_or_none(post.get('commentsCount')),
            'age_limit': 18 if post.get('nsfw') == 1 else None,
            'categories': [section] if section else None,
            'tags': tags,
        }
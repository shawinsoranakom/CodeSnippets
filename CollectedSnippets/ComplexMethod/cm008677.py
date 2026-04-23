def _parse_post(self, post_data):
        post_id = post_data['hash']
        lead_content = self._parse_json(post_data.get('lead_content') or '{}', post_id, fatal=False) or {}
        description, full_description = post_data.get('leadStr') or self._parse_content_as_text(
            self._parse_json(post_data.get('lead_content'), post_id)), None
        if post_data.get('has_article'):
            article_content = self._parse_json(
                post_data.get('article_content')
                or self._call_api(f'web/posts/article/{post_data.get("id", post_id)}', post_id,
                                  note='Downloading article metadata', errnote='Unable to download article metadata', fatal=False).get('article'),
                post_id, fatal=False)
            full_description = self._parse_content_as_text(article_content)

        user_data = post_data.get('user') or {}
        info_dict = {
            'extractor_key': GameJoltIE.ie_key(),
            'extractor': 'GameJolt',
            'webpage_url': str_or_none(post_data.get('url')) or f'https://gamejolt.com/p/{post_id}',
            'id': post_id,
            'title': description,
            'description': full_description or description,
            'display_id': post_data.get('slug'),
            'uploader': user_data.get('display_name') or user_data.get('name'),
            'uploader_id': user_data.get('username'),
            'uploader_url': format_field(user_data, 'url', 'https://gamejolt.com%s'),
            'categories': [try_get(category, lambda x: '{} - {}'.format(x['community']['name'], x['channel'].get('display_title') or x['channel']['title']))
                           for category in post_data.get('communities') or []],
            'tags': traverse_obj(
                lead_content, ('content', ..., 'content', ..., 'marks', ..., 'attrs', 'tag'), expected_type=str_or_none),
            'like_count': int_or_none(post_data.get('like_count')),
            'comment_count': int_or_none(post_data.get('comment_count'), default=0),
            'timestamp': int_or_none(post_data.get('added_on'), scale=1000),
            'release_timestamp': int_or_none(post_data.get('published_on'), scale=1000),
            '__post_extractor': self.extract_comments(post_data.get('id'), post_id),
        }

        # TODO: Handle multiple videos/embeds?
        video_data = traverse_obj(post_data, ('videos', ...), expected_type=dict, get_all=False) or {}
        formats, subtitles, thumbnails = [], {}, []
        for media in video_data.get('media') or []:
            media_url, mimetype, ext, media_id = media['img_url'], media.get('filetype', ''), determine_ext(media['img_url']), media.get('type')
            if mimetype == 'application/vnd.apple.mpegurl' or ext == 'm3u8':
                hls_formats, hls_subs = self._extract_m3u8_formats_and_subtitles(media_url, post_id, 'mp4', m3u8_id=media_id)
                formats.extend(hls_formats)
                subtitles.update(hls_subs)
            elif mimetype == 'application/dash+xml' or ext == 'mpd':
                dash_formats, dash_subs = self._extract_mpd_formats_and_subtitles(media_url, post_id, mpd_id=media_id)
                formats.extend(dash_formats)
                subtitles.update(dash_subs)
            elif 'image' in mimetype:
                thumbnails.append({
                    'id': media_id,
                    'url': media_url,
                    'width': media.get('width'),
                    'height': media.get('height'),
                    'filesize': media.get('filesize'),
                })
            else:
                formats.append({
                    'format_id': media_id,
                    'url': media_url,
                    'width': media.get('width'),
                    'height': media.get('height'),
                    'filesize': media.get('filesize'),
                    'acodec': 'none' if 'video-card' in media_url else None,
                })

        if formats:
            return {
                **info_dict,
                'formats': formats,
                'subtitles': subtitles,
                'thumbnails': thumbnails,
                'view_count': int_or_none(video_data.get('view_count')),
            }

        gif_entries = []
        for media in post_data.get('media', []):
            if determine_ext(media['img_url']) != 'gif' or 'gif' not in media.get('filetype', ''):
                continue
            gif_entries.append({
                'id': media['hash'],
                'title': media['filename'].split('.')[0],
                'formats': [{
                    'format_id': url_key,
                    'url': media[url_key],
                    'width': media.get('width') if url_key == 'img_url' else None,
                    'height': media.get('height') if url_key == 'img_url' else None,
                    'filesize': media.get('filesize') if url_key == 'img_url' else None,
                    'acodec': 'none',
                } for url_key in ('img_url', 'mediaserver_url', 'mediaserver_url_mp4', 'mediaserver_url_webm') if media.get(url_key)],
            })
        if gif_entries:
            return {
                '_type': 'playlist',
                **info_dict,
                'entries': gif_entries,
            }

        embed_url = traverse_obj(post_data, ('embeds', ..., 'url'), expected_type=str_or_none, get_all=False)
        if embed_url:
            return self.url_result(embed_url)
        return info_dict
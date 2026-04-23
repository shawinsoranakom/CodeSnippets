def _real_extract(self, url):
        site, path, display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, display_id)
        drupal_settings = self._parse_json(self._search_regex(
            r'<script[^>]+?data-drupal-selector="drupal-settings-json"[^>]*?>({.+?})</script>',
            webpage, 'drupal setting'), display_id)
        video_data = next(v for v in drupal_settings['turner_playlist'] if v.get('url') == path)

        media_id = video_data['mediaID']
        title = video_data['title']
        tokenizer_query = compat_parse_qs(compat_urllib_parse_urlparse(
            drupal_settings['ngtv_token_url']).query)

        info = self._extract_ngtv_info(
            media_id, tokenizer_query, {
                'url': url,
                'site_name': site[:3].upper(),
                'auth_required': video_data.get('authRequired') == '1',
            })

        thumbnails = []
        for image_id, image in video_data.get('images', {}).items():
            image_url = image.get('url')
            if not image_url or image.get('type') != 'video':
                continue
            i = {
                'id': image_id,
                'url': image_url,
            }
            mobj = re.search(r'(\d+)x(\d+)', image_url)
            if mobj:
                i.update({
                    'width': int(mobj.group(1)),
                    'height': int(mobj.group(2)),
                })
            thumbnails.append(i)

        info.update({
            'id': media_id,
            'title': title,
            'description': strip_or_none(video_data.get('descriptionNoTags') or video_data.get('shortDescriptionNoTags')),
            'duration': float_or_none(video_data.get('duration')) or info.get('duration'),
            'timestamp': int_or_none(video_data.get('created')),
            'season_number': int_or_none(video_data.get('season')),
            'episode_number': int_or_none(video_data.get('episode')),
            'thumbnails': thumbnails,
        })
        return info
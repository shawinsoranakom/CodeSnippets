def _real_extract(self, url):
        site, path, display_id, watch = self._match_valid_url(url).group('site', 'path', 'id', 'watch')
        is_live = bool(watch)
        webpage = self._download_webpage(url, display_id)
        drupal_settings = self._search_json(
            r'<script\b[^>]+\bdata-drupal-selector="drupal-settings-json"[^>]*>',
            webpage, 'drupal settings', display_id)
        video_data = next(v for v in drupal_settings['turner_playlist'] if is_live or v.get('url') == path)

        media_id = video_data['mediaID']
        title = video_data['title']
        tokenizer_query = urllib.parse.parse_qs(urllib.parse.urlparse(
            drupal_settings['ngtv_token_url']).query)

        auth_info = traverse_obj(drupal_settings, ('top2', {dict})) or {}
        site_name = auth_info.get('siteName') or self._SITE_INFO[site][0]
        software_statement = auth_info.get('softwareStatement') or self._SITE_INFO[site][1]

        info = self._extract_ngtv_info(
            media_id, tokenizer_query, software_statement, {
                'url': url,
                'site_name': site_name,
                'auth_required': video_data.get('authRequired') == '1' or is_live,
                'is_live': is_live,
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
            'is_live': is_live,
        })
        if site == 'trutv':
            info['_old_archive_ids'] = [make_archive_id(site, media_id)]
        return info
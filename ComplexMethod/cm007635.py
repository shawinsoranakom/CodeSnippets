def _real_extract(self, url):
        twid = self._match_id(url)
        status = self._call_api(
            'statuses/show/%s.json' % twid, twid, {
                'cards_platform': 'Web-12',
                'include_cards': 1,
                'include_reply_count': 1,
                'include_user_entities': 0,
                'tweet_mode': 'extended',
            })

        title = description = status['full_text'].replace('\n', ' ')
        # strip  'https -_t.co_BJYgOjSeGA' junk from filenames
        title = re.sub(r'\s+(https?://[^ ]+)', '', title)
        user = status.get('user') or {}
        uploader = user.get('name')
        if uploader:
            title = '%s - %s' % (uploader, title)
        uploader_id = user.get('screen_name')

        tags = []
        for hashtag in (try_get(status, lambda x: x['entities']['hashtags'], list) or []):
            hashtag_text = hashtag.get('text')
            if not hashtag_text:
                continue
            tags.append(hashtag_text)

        info = {
            'id': twid,
            'title': title,
            'description': description,
            'uploader': uploader,
            'timestamp': unified_timestamp(status.get('created_at')),
            'uploader_id': uploader_id,
            'uploader_url': 'https://twitter.com/' + uploader_id if uploader_id else None,
            'like_count': int_or_none(status.get('favorite_count')),
            'repost_count': int_or_none(status.get('retweet_count')),
            'comment_count': int_or_none(status.get('reply_count')),
            'age_limit': 18 if status.get('possibly_sensitive') else 0,
            'tags': tags,
        }

        def extract_from_video_info(media):
            video_info = media.get('video_info') or {}

            formats = []
            for variant in video_info.get('variants', []):
                formats.extend(self._extract_variant_formats(variant, twid))
            self._sort_formats(formats)

            thumbnails = []
            media_url = media.get('media_url_https') or media.get('media_url')
            if media_url:
                def add_thumbnail(name, size):
                    thumbnails.append({
                        'id': name,
                        'url': update_url_query(media_url, {'name': name}),
                        'width': int_or_none(size.get('w') or size.get('width')),
                        'height': int_or_none(size.get('h') or size.get('height')),
                    })
                for name, size in media.get('sizes', {}).items():
                    add_thumbnail(name, size)
                add_thumbnail('orig', media.get('original_info') or {})

            info.update({
                'formats': formats,
                'thumbnails': thumbnails,
                'duration': float_or_none(video_info.get('duration_millis'), 1000),
            })

        media = try_get(status, lambda x: x['extended_entities']['media'][0])
        if media and media.get('type') != 'photo':
            extract_from_video_info(media)
        else:
            card = status.get('card')
            if card:
                binding_values = card['binding_values']

                def get_binding_value(k):
                    o = binding_values.get(k) or {}
                    return try_get(o, lambda x: x[x['type'].lower() + '_value'])

                card_name = card['name'].split(':')[-1]
                if card_name == 'player':
                    info.update({
                        '_type': 'url',
                        'url': get_binding_value('player_url'),
                    })
                elif card_name == 'periscope_broadcast':
                    info.update({
                        '_type': 'url',
                        'url': get_binding_value('url') or get_binding_value('player_url'),
                        'ie_key': PeriscopeIE.ie_key(),
                    })
                elif card_name == 'broadcast':
                    info.update({
                        '_type': 'url',
                        'url': get_binding_value('broadcast_url'),
                        'ie_key': TwitterBroadcastIE.ie_key(),
                    })
                elif card_name == 'summary':
                    info.update({
                        '_type': 'url',
                        'url': get_binding_value('card_url'),
                    })
                elif card_name == 'unified_card':
                    media_entities = self._parse_json(get_binding_value('unified_card'), twid)['media_entities']
                    extract_from_video_info(next(iter(media_entities.values())))
                # amplify, promo_video_website, promo_video_convo, appplayer,
                # video_direct_message, poll2choice_video, poll3choice_video,
                # poll4choice_video, ...
                else:
                    is_amplify = card_name == 'amplify'
                    vmap_url = get_binding_value('amplify_url_vmap') if is_amplify else get_binding_value('player_stream_url')
                    content_id = get_binding_value('%s_content_id' % (card_name if is_amplify else 'player'))
                    formats = self._extract_formats_from_vmap_url(vmap_url, content_id or twid)
                    self._sort_formats(formats)

                    thumbnails = []
                    for suffix in ('_small', '', '_large', '_x_large', '_original'):
                        image = get_binding_value('player_image' + suffix) or {}
                        image_url = image.get('url')
                        if not image_url or '/player-placeholder' in image_url:
                            continue
                        thumbnails.append({
                            'id': suffix[1:] if suffix else 'medium',
                            'url': image_url,
                            'width': int_or_none(image.get('width')),
                            'height': int_or_none(image.get('height')),
                        })

                    info.update({
                        'formats': formats,
                        'thumbnails': thumbnails,
                        'duration': int_or_none(get_binding_value(
                            'content_duration_seconds')),
                    })
            else:
                expanded_url = try_get(status, lambda x: x['entities']['urls'][0]['expanded_url'])
                if not expanded_url:
                    raise ExtractorError("There's no video in this tweet.")
                info.update({
                    '_type': 'url',
                    'url': expanded_url,
                })
        return info
def extract_from_card_info(card):
            if not card:
                return

            card_name = card['name'].split(':')[-1]
            self.write_debug(f'Extracting from {card_name} card info: {card.get("url")}')
            binding_values = card['binding_values']

            def get_binding_value(k):
                o = binding_values.get(k) or {}
                return try_get(o, lambda x: x[x['type'].lower() + '_value'])

            if card_name == 'player':
                yield {
                    '_type': 'url',
                    'url': get_binding_value('player_url'),
                }
            elif card_name == 'periscope_broadcast':
                yield {
                    '_type': 'url',
                    'url': get_binding_value('url') or get_binding_value('player_url'),
                    'ie_key': PeriscopeIE.ie_key(),
                }
            elif card_name == 'broadcast':
                yield {
                    '_type': 'url',
                    'url': get_binding_value('broadcast_url'),
                    'ie_key': TwitterBroadcastIE.ie_key(),
                }
            elif card_name == 'audiospace':
                yield {
                    '_type': 'url',
                    'url': f'https://twitter.com/i/spaces/{get_binding_value("id")}',
                    'ie_key': TwitterSpacesIE.ie_key(),
                }
            elif card_name == 'summary':
                yield {
                    '_type': 'url',
                    'url': get_binding_value('card_url'),
                }
            elif card_name == 'unified_card':
                unified_card = self._parse_json(get_binding_value('unified_card'), twid)
                yield from map(extract_from_video_info, traverse_obj(
                    unified_card, ('media_entities', lambda _, v: v['type'] == 'video')))
            # amplify, promo_video_website, promo_video_convo, appplayer,
            # video_direct_message, poll2choice_video, poll3choice_video,
            # poll4choice_video, ...
            else:
                is_amplify = card_name == 'amplify'
                vmap_url = get_binding_value('amplify_url_vmap') if is_amplify else get_binding_value('player_stream_url')
                content_id = get_binding_value('%s_content_id' % (card_name if is_amplify else 'player'))
                formats, subtitles = self._extract_formats_from_vmap_url(vmap_url, content_id or twid)

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

                yield {
                    'formats': formats,
                    'subtitles': subtitles,
                    'thumbnails': thumbnails,
                    'duration': int_or_none(get_binding_value(
                        'content_duration_seconds')),
                }
def parse_media(media):
                if not media:
                    return
                for item in (try_get(media, lambda x: x['media']['items'], list) or []):
                    item_id = item.get('id')
                    item_title = item.get('title')
                    if not (item_id and item_title):
                        continue
                    formats, subtitles = self._download_media_selector(item_id)
                    item_desc = None
                    blocks = try_get(media, lambda x: x['summary']['blocks'], list)
                    if blocks:
                        summary = []
                        for block in blocks:
                            text = try_get(block, lambda x: x['model']['text'], str)
                            if text:
                                summary.append(text)
                        if summary:
                            item_desc = '\n\n'.join(summary)
                    item_time = None
                    for meta in try_get(media, lambda x: x['metadata']['items'], list) or []:
                        if try_get(meta, lambda x: x['label']) == 'Published':
                            item_time = unified_timestamp(meta.get('timestamp'))
                            break
                    entries.append({
                        'id': item_id,
                        'title': item_title,
                        'thumbnail': item.get('holdingImageUrl'),
                        'formats': formats,
                        'subtitles': subtitles,
                        'timestamp': item_time,
                        'description': strip_or_none(item_desc),
                        'duration': int_or_none(item.get('duration')),
                    })
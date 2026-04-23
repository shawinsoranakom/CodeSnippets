def _extract_episode(self, episode, series):
        episode_id = episode['id']
        title = episode['name'].strip()

        formats = []
        audio_preview = episode.get('audioPreview') or {}
        audio_preview_url = audio_preview.get('url')
        if audio_preview_url:
            f = {
                'url': audio_preview_url.replace('://p.scdn.co/mp3-preview/', '://anon-podcast.scdn.co/'),
                'vcodec': 'none',
            }
            audio_preview_format = audio_preview.get('format')
            if audio_preview_format:
                f['format_id'] = audio_preview_format
                mobj = re.match(r'([0-9A-Z]{3})_(?:[A-Z]+_)?(\d+)', audio_preview_format)
                if mobj:
                    f.update({
                        'abr': int(mobj.group(2)),
                        'ext': mobj.group(1).lower(),
                    })
            formats.append(f)

        for item in (try_get(episode, lambda x: x['audio']['items']) or []):
            item_url = item.get('url')
            if not (item_url and item.get('externallyHosted')):
                continue
            formats.append({
                'url': clean_podcast_url(item_url),
                'vcodec': 'none',
            })

        thumbnails = []
        for source in (try_get(episode, lambda x: x['coverArt']['sources']) or []):
            source_url = source.get('url')
            if not source_url:
                continue
            thumbnails.append({
                'url': source_url,
                'width': int_or_none(source.get('width')),
                'height': int_or_none(source.get('height')),
            })

        return {
            'id': episode_id,
            'title': title,
            'formats': formats,
            'thumbnails': thumbnails,
            'description': strip_or_none(episode.get('description')),
            'duration': float_or_none(try_get(
                episode, lambda x: x['duration']['totalMilliseconds']), 1000),
            'release_date': unified_strdate(try_get(
                episode, lambda x: x['releaseDate']['isoString'])),
            'series': series,
        }
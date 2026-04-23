def _real_extract(self, url):
        program_slug, slug = re.match(self._VALID_URL, url).groups()
        video = self._download_json(
            'https://www.tf1.fr/graphql/web', slug, query={
                'id': '9b80783950b85247541dd1d851f9cc7fa36574af015621f853ab111a679ce26f',
                'variables': json.dumps({
                    'programSlug': program_slug,
                    'slug': slug,
                })
            })['data']['videoBySlug']
        wat_id = video['streamId']

        tags = []
        for tag in (video.get('tags') or []):
            label = tag.get('label')
            if not label:
                continue
            tags.append(label)

        decoration = video.get('decoration') or {}

        thumbnails = []
        for source in (try_get(decoration, lambda x: x['image']['sources'], list) or []):
            source_url = source.get('url')
            if not source_url:
                continue
            thumbnails.append({
                'url': source_url,
                'width': int_or_none(source.get('width')),
            })

        return {
            '_type': 'url_transparent',
            'id': wat_id,
            'url': 'wat:' + wat_id,
            'title': video.get('title'),
            'thumbnails': thumbnails,
            'description': decoration.get('description'),
            'timestamp': parse_iso8601(video.get('date')),
            'duration': int_or_none(try_get(video, lambda x: x['publicPlayingInfos']['duration'])),
            'tags': tags,
            'series': decoration.get('programLabel'),
            'season_number': int_or_none(video.get('season')),
            'episode_number': int_or_none(video.get('episode')),
        }
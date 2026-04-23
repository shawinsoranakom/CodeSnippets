def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        next_data = self._search_nextjs_data(webpage, display_id)
        episode = next_data['props']['pageProps']['episode']

        video_id = episode['id']
        title = episode.get('title') or self._generic_title('', webpage)
        url = episode['m3u8']
        formats = self._extract_m3u8_formats(url, display_id, ext='ts')

        show = traverse_obj(episode, ('show', 'title'))
        show_id = traverse_obj(episode, ('show', 'id'))

        show_json = None
        app_slug = (self._html_search_regex(
            '<script\\s+src=["\']/_next/static/([-_a-zA-Z0-9]+)/_',
            webpage, 'app slug', fatal=False) or next_data.get('buildId'))
        show_slug = traverse_obj(episode, ('show', 'linkObj', 'resourceUrl'))
        if app_slug and show_slug and '/' in show_slug:
            show_slug = show_slug.rsplit('/', 1)[1]
            show_json_url = f'https://www.callin.com/_next/data/{app_slug}/show/{show_slug}.json'
            show_json = self._download_json(show_json_url, display_id, fatal=False)

        host = (traverse_obj(show_json, ('pageProps', 'show', 'hosts', 0))
                or traverse_obj(episode, ('speakers', 0)))

        host_nick = traverse_obj(host, ('linkObj', 'resourceUrl'))
        host_nick = host_nick.rsplit('/', 1)[1] if (host_nick and '/' in host_nick) else None

        cast = list(filter(None, [
            self.try_get_user_name(u) for u in
            traverse_obj(episode, (('speakers', 'callerTags'), ...)) or []
        ]))

        episode_list = traverse_obj(show_json, ('pageProps', 'show', 'episodes')) or []
        episode_number = next(
            (len(episode_list) - i for i, e in enumerate(episode_list) if e.get('id') == video_id),
            None)

        return {
            'id': video_id,
            '_old_archive_ids': [make_archive_id(self, display_id.rsplit('-', 1)[-1])],
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': traverse_obj(episode, ('show', 'photo')),
            'description': episode.get('description'),
            'uploader': self.try_get_user_name(host) if host else None,
            'timestamp': episode.get('publishedAt'),
            'uploader_id': host_nick,
            'uploader_url': traverse_obj(show_json, ('pageProps', 'show', 'url')),
            'channel': show,
            'channel_id': show_id,
            'channel_url': traverse_obj(episode, ('show', 'linkObj', 'resourceUrl')),
            'duration': float_or_none(episode.get('runtime')),
            'view_count': int_or_none(episode.get('plays')),
            'categories': traverse_obj(episode, ('show', 'categorizations', ..., 'name')),
            'cast': cast if cast else None,
            'series': show,
            'series_id': show_id,
            'episode': title,
            'episode_number': episode_number,
            'episode_id': video_id,
        }
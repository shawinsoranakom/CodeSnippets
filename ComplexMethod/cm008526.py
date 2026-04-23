def _real_extract(self, url):
        video_id = self._match_id(url)
        url_lang = 'fr' if any(x in url for x in ('/emission?', '/rechercher?')) else 'en'
        pl_type, list_type = ('program', 'itemList') if any(x in url for x in ('/program?', '/emission?')) else ('search', 'searchResult')
        api_url = (
            f'https://www.cpac.ca/api/1/services/contentModel.json?url=/site/website/{pl_type}/index.xml&crafterSite=cpacca&{video_id}')
        content = self._download_json(api_url, video_id)
        entries = []
        total_pages = int_or_none(try_get(content, lambda x: x['page'][list_type]['totalPages']), default=1)
        for page in range(1, total_pages + 1):
            if page > 1:
                api_url = update_url_query(api_url, {'page': page})
                content = self._download_json(
                    api_url, video_id,
                    note=f'Downloading continuation - {page}',
                    fatal=False)

            for item in try_get(content, lambda x: x['page'][list_type]['item'], list) or []:
                episode_url = urljoin(url, try_get(item, lambda x: x[f'url_{url_lang}_s']))
                if episode_url:
                    entries.append(episode_url)

        return self.playlist_result(
            (self.url_result(entry) for entry in entries),
            playlist_id=video_id,
            playlist_title=try_get(content, lambda x: x['page']['program'][f'title_{url_lang}_t']) or video_id.split('=')[-1],
            playlist_description=try_get(content, lambda x: x['page']['program'][f'description_{url_lang}_t']),
        )
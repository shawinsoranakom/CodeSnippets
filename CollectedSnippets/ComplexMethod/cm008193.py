def _entries(self, url, playlist_id):
        for page in itertools.count(1):
            try:
                webpage = self._download_webpage(
                    f'{url}/{page}', playlist_id, f'Downloading page {page}')
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status == 404:
                    break
                raise

            episodes = get_elements_html_by_class('tm-ouvir-podcast', webpage)
            if not episodes:
                break
            for url_path in traverse_obj(episodes, (..., {extract_attributes}, 'href')):
                episode_url = urljoin(url, url_path)
                if RadioComercialIE.suitable(episode_url):
                    yield episode_url
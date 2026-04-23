def _download_ytcfg(self, client, video_id):
        url = {
            'mweb': 'https://m.youtube.com',
            'web': 'https://www.youtube.com',
            'web_safari': 'https://www.youtube.com',
            'web_music': 'https://music.youtube.com',
            'web_creator': 'https://studio.youtube.com',
            'web_embedded': f'https://www.youtube.com/embed/{video_id}?html5=1',
            'tv': 'https://www.youtube.com/tv',
        }.get(client)
        if not url:
            return {}

        default_ytcfg = self._get_default_ytcfg(client)

        if default_ytcfg['REQUIRE_AUTH'] and not self.is_authenticated:
            return {}

        webpage = self._download_webpage_with_retries(
            url, video_id, note=f'Downloading {client.replace("_", " ").strip()} client config',
            headers=traverse_obj(default_ytcfg, {
                'User-Agent': ('INNERTUBE_CONTEXT', 'client', 'userAgent', {str}),
                'Referer': ('INNERTUBE_CONTEXT', 'thirdParty', 'embedUrl', {str}),
            }))

        ytcfg = self.extract_ytcfg(video_id, webpage) or {}

        # See https://github.com/yt-dlp/yt-dlp/issues/14826
        if _split_innertube_client(client)[2] == 'embedded':
            _fix_embedded_ytcfg(ytcfg)

        # Workaround for https://github.com/yt-dlp/yt-dlp/issues/12563
        # But it's not effective when logged-in
        if client == 'tv' and not self.is_authenticated:
            config_info = traverse_obj(ytcfg, (
                'INNERTUBE_CONTEXT', 'client', 'configInfo', {dict})) or {}
            config_info.pop('appInstallData', None)

        return ytcfg
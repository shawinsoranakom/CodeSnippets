def _real_extract(self, url):
        pl_id = self._match_id(url)

        if self._downloader.params.get('noplaylist'):
            self.to_screen('Downloading just the featured video because of --no-playlist')
            return self.url_result(self._get_video_url(url), 'ThisVid')

        self.to_screen(
            'Downloading playlist %s - add --no-playlist to download just the featured video' % (pl_id, ))
        result = super(ThisVidPlaylistIE, self)._real_extract(url)

        # rework title returned as `the title - the title`
        title = result['title']
        t_len = len(title)
        if t_len > 5 and t_len % 2 != 0:
            t_len = t_len // 2
            if title[t_len] == '-':
                title = [t.strip() for t in (title[:t_len], title[t_len + 1:])]
                if title[0] and title[0] == title[1]:
                    result['title'] = title[0]
        return result
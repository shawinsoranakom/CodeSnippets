def _real_extract(self, url):
        article_id = self._match_id(url)

        article = self._download_json(
            'https://www.phoenix.de/response/id/%s' % article_id, article_id,
            'Downloading article JSON')

        video = article['absaetze'][0]
        title = video.get('titel') or article.get('subtitel')

        if video.get('typ') == 'video-youtube':
            video_id = video['id']
            return self.url_result(
                video_id, ie=YoutubeIE.ie_key(), video_id=video_id,
                video_title=title)

        video_id = compat_str(video.get('basename') or video.get('content'))

        details = self._download_json(
            'https://www.phoenix.de/php/mediaplayer/data/beitrags_details.php',
            video_id, 'Downloading details JSON', query={
                'ak': 'web',
                'ptmd': 'true',
                'id': video_id,
                'profile': 'player2',
            })

        title = title or details['title']
        content_id = details['tracking']['nielsen']['content']['assetid']

        info = self._extract_ptmd(
            'https://tmd.phoenix.de/tmd/2/ngplayer_2_3/vod/ptmd/phoenix/%s' % content_id,
            content_id, None, url)

        duration = int_or_none(try_get(
            details, lambda x: x['tracking']['nielsen']['content']['length']))
        timestamp = unified_timestamp(details.get('editorialDate'))
        series = try_get(
            details, lambda x: x['tracking']['nielsen']['content']['program'],
            compat_str)
        episode = title if details.get('contentType') == 'episode' else None

        thumbnails = []
        teaser_images = try_get(details, lambda x: x['teaserImageRef']['layouts'], dict) or {}
        for thumbnail_key, thumbnail_url in teaser_images.items():
            thumbnail_url = urljoin(url, thumbnail_url)
            if not thumbnail_url:
                continue
            thumbnail = {
                'url': thumbnail_url,
            }
            m = re.match('^([0-9]+)x([0-9]+)$', thumbnail_key)
            if m:
                thumbnail['width'] = int(m.group(1))
                thumbnail['height'] = int(m.group(2))
            thumbnails.append(thumbnail)

        return merge_dicts(info, {
            'id': content_id,
            'title': title,
            'description': details.get('leadParagraph'),
            'duration': duration,
            'thumbnails': thumbnails,
            'timestamp': timestamp,
            'uploader': details.get('tvService'),
            'series': series,
            'episode': episode,
        })
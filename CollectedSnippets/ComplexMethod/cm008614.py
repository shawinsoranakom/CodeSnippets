def _extract_info(self, webpage, video_id=None, ppn=None):
        if not video_id:
            video_id = self._search_regex(
                r'data-nid=([\'"])(?P<vid>\d+)\1',
                webpage, 'video_id', group='vid')

        media_url = self._search_regex(
            (r'src\s*:\s*([\'"])(?P<url>\S+?mp3.+?)\1',
             r'data-podcast\s*=\s*([\'"])(?P<url>\S+?mp3.+?)\1'),
            webpage, 'media_url', group='url')
        formats = [{
            'url': media_url,
            'format_id': 'http-mp3',
            'ext': 'mp3',
            'acodec': 'mp3',
            'vcodec': 'none',
        }]

        title = self._html_search_regex(
            (r'<div class="title">(?P<title>.+?)</',
             r'<title>(?P<title>[^<]+)</title>',
             r'title:\s*([\'"])(?P<title>.+?)\1'),
            webpage, 'title', group='title')

        description = (
            self._html_search_regex(
                (r'<div class="description">(.+?)</div>',
                 r'<div class="description-mobile">(.+?)</div>',
                 r'<div class="box-txt">([^<]+?)</div>',
                 r'<div class="field-content"><p>(.+?)</p></div>'),
                webpage, 'description', default=None)
            or self._html_search_meta('description', webpage))

        thumb = self._html_search_regex(
            (r'<div class="podcast-image"><img src="(.+?)"></div>',
             r'<div class="container-embed"[^<]+url\((.+?)\);">',
             r'<div class="field-content"><img src="(.+?)"'),
            webpage, 'thumbnail', fatal=False, default=None)

        duration = parse_duration(self._html_search_regex(
            r'<span class="(?:durata|duration)">([\d:]+)</span>',
            webpage, 'duration', fatal=False, default=None))

        date = self._html_search_regex(
            r'class="data">\s*(?:<span>)?([\d\.]+)\s*</',
            webpage, 'date', default=None)

        date_alt = self._search_regex(
            r'(\d+[\./]\d+[\./]\d+)', title, 'date_alt', default=None)
        ppn = ppn or self._search_regex(
            r'ppN:\s*([\'"])(?P<ppn>.+?)\1',
            webpage, 'ppn', group='ppn', default=None)
        # if the date is not in the title
        # and title is the same as the show_title
        # add the date to the title
        if date and not date_alt and ppn and ppn.lower() == title.lower():
            title = f'{title} del {date}'
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': float_or_none(duration),
            'formats': formats,
            'thumbnail': thumb,
            'upload_date': unified_strdate(date),
        }
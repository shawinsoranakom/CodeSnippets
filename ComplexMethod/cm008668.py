def _extract_brightcove_urls(cls, webpage):
        """Return a list of all Brightcove URLs from the webpage """

        url_m = re.search(
            r'''(?x)
                <meta\s+
                    (?:property|itemprop)=([\'"])(?:og:video|embedURL)\1[^>]+
                    content=([\'"])(?P<url>https?://(?:secure|c)\.brightcove.com/(?:(?!\2).)+)\2
            ''', webpage)
        if url_m:
            url = unescapeHTML(url_m.group('url'))
            # Some sites don't add it, we can't download with this url, for example:
            # http://www.ktvu.com/videos/news/raw-video-caltrain-releases-video-of-man-almost/vCTZdY/
            if 'playerKey' in url or 'videoId' in url or 'idVideo' in url:
                return [url]

        matches = re.findall(
            r'''(?sx)<object
            (?:
                [^>]+?class=[\'"][^>]*?BrightcoveExperience.*?[\'"] |
                [^>]*?>\s*<param\s+name="movie"\s+value="https?://[^/]*brightcove\.com/
            ).+?>\s*</object>''',
            webpage)
        if matches:
            return list(filter(None, [cls._build_brightcove_url(m) for m in matches]))

        matches = re.findall(r'(customBC\.createVideo\(.+?\);)', webpage)
        if matches:
            return list(filter(None, [
                cls._build_brightcove_url_from_js(custom_bc)
                for custom_bc in matches]))
        return [src for _, src in re.findall(
            r'<iframe[^>]+src=([\'"])((?:https?:)?//link\.brightcove\.com/services/player/(?!\1).+)\1', webpage)]
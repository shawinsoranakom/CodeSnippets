def _fix_path(url):
        # an embedded /../ or /./ sequence is not automatically handled by urllib2
        # see https://github.com/yt-dlp/yt-dlp/issues/3355
        parsed_url = compat_urllib_parse.urlsplit(url)
        path = parsed_url.path
        if not path.endswith('/'):
            path += '/'
        parts = path.partition('/./')
        if not parts[1]:
            parts = path.partition('/../')
        if parts[1]:
            path = compat_urllib_parse.urljoin(
                parts[0] + parts[1][:1],
                parts[1][1:] + (parts[2] if parsed_url.path.endswith('/') else parts[2][:-1]))
            url = parsed_url._replace(path=path).geturl()
        if '/.' in url:
            # worse, URL path may have initial /../ against RFCs: work-around
            # by stripping such prefixes, like eg Firefox
            path = parsed_url.path + '/'
            while path.startswith('/.'):
                if path.startswith('/../'):
                    path = path[3:]
                elif path.startswith('/./'):
                    path = path[2:]
                else:
                    break
            path = path[:-1]
            if not path.startswith('/') and parsed_url.path.startswith('/'):
                path = '/' + path
            url = parsed_url._replace(path=path).geturl()
        return url
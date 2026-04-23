def _download_webpage_handle(self, url, video_id, *args, **kwargs):
        # specialised to (a) use vanilla UA (b) detect geo-block
        params = self._downloader.params
        nkwargs = {}
        if (
                'user_agent' not in params
                and not any(re.match(r'(?i)user-agent\s*:', h)
                            for h in (params.get('headers') or []))
                and 'User-Agent' not in (kwargs.get('headers') or {})):

            kwargs.setdefault('headers', {})
            kwargs['headers'] = self._vanilla_ua_header()
            nkwargs = kwargs
        if kwargs.get('expected_status') is not None:
            exp = kwargs['expected_status']
            if isinstance(exp, compat_integer_types):
                exp = [exp]
            if isinstance(exp, (list, tuple)) and 403 not in exp:
                kwargs['expected_status'] = [403]
                kwargs['expected_status'].extend(exp)
                nkwargs = kwargs
        else:
            kwargs['expected_status'] = 403
            nkwargs = kwargs

        if nkwargs:
            kwargs = compat_kwargs(kwargs)

        ret = super(ITVBaseIE, self)._download_webpage_handle(url, video_id, *args, **kwargs)
        if ret is False:
            return ret
        webpage, urlh = ret

        if urlh.getcode() == 403:
            # geo-block error is like this, with an unnecessary 'Of':
            # '{\n  "Message" : "Request Originated Outside Of Allowed Geographic Region",\
            # \n  "TransactionId" : "oas-magni-475082-xbYF0W"\n}'
            if '"Request Originated Outside Of Allowed Geographic Region"' in webpage:
                self.raise_geo_restricted(countries=['GB'])
            ret = self.__handle_request_webpage_error(
                compat_HTTPError(urlh.geturl(), 403, 'HTTP Error 403: Forbidden', urlh.headers, urlh),
                fatal=kwargs.get('fatal'))

        return ret
def download_by_url(self, url, **kwargs):
        self.url = url
        self.vid = None

        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            set_proxy(parse_host(kwargs['extractor_proxy']))
        self.prepare(**kwargs)
        if self.out:
            return
        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            unset_proxy()

        try:
            self.streams_sorted = [dict([('id', stream_type['id'])] + list(self.streams[stream_type['id']].items())) for stream_type in self.__class__.stream_types if stream_type['id'] in self.streams]
        except:
            self.streams_sorted = [dict([('itag', stream_type['itag'])] + list(self.streams[stream_type['itag']].items())) for stream_type in self.__class__.stream_types if stream_type['itag'] in self.streams]

        self.extract(**kwargs)

        self.download(**kwargs)
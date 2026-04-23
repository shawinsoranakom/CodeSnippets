def prepare(self, vid = '', title = None, **kwargs):
        assert vid

        api_url = self.API_ENDPOINT + \
            'servlet/playinfo?vid={vid}&m=0'.format(vid = vid)  #return XML

        html = get_content(api_url)
        self.tree = ET.ElementTree(ET.fromstring(html))

        if self.tree.find('result').text != '1':
            log.wtf('API result says failed!')
            raise 

        if title is None:
            self.title = '_'.join([i.text for i in self.tree.iterfind('video/videomarks/videomark/markdesc')])
        else:
            self.title = title

        if not title:
            self.title = vid

        for i in self.tree.iterfind('video/quality'):
            quality = i.attrib ['value']
            url = i[0].attrib['playurl']
            self.stream_types.append({'id': quality,
                                      'video_profile': i.attrib ['desp']})
            self.streams[quality] = {'url': url,
                                     'video_profile': i.attrib ['desp']}
            self.streams_sorted = [dict([('id', stream_type['id'])] + list(self.streams[stream_type['id']].items())) for stream_type in self.__class__.stream_types if stream_type['id'] in self.streams]
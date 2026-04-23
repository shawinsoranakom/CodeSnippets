def download(self, **kwargs):

        if 'stream_id' in kwargs and kwargs['stream_id']:
            stream_id = kwargs['stream_id']
        else:
            stream_id = 'null'

        # print video info only
        if 'info_only' in kwargs and kwargs['info_only']:
            if stream_id != 'null':
                if 'index' not in kwargs:
                    self.p(stream_id)
                else:
                    self.p_i(stream_id)
            else:
                # Display all available streams
                if 'index' not in kwargs:
                    self.p([])
                else:
                    stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else \
                        self.streams_sorted[0]['itag']
                    self.p_i(stream_id)

        # default to use the best quality
        if stream_id == 'null':
            stream_id = self.streams_sorted[0]['id']

        stream_info = self.streams[stream_id]

        if not kwargs['info_only']:
            if player:
                # with m3u8 format because some video player can process urls automatically (e.g. mpv)
                launch_player(player, [stream_info['m3u8_url']])
            else:
                download_urls(stream_info['src'], self.title, stream_info['container'], stream_info['size'],
                              output_dir=kwargs['output_dir'],
                              merge=kwargs.get('merge', True),
                              headers={'Referer': self.url})
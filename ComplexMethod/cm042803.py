def download(self, **kwargs):
        if 'json_output' in kwargs and kwargs['json_output']:
            json_output.output(self)
        elif 'info_only' in kwargs and kwargs['info_only']:
            if 'stream_id' in kwargs and kwargs['stream_id']:
                # Display the stream
                stream_id = kwargs['stream_id']
                if 'index' not in kwargs:
                    self.p(stream_id)
                else:
                    self.p_i(stream_id)
            else:
                # Display all available streams
                if 'index' not in kwargs:
                    self.p([])
                else:
                    stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else self.streams_sorted[0]['itag']
                    self.p_i(stream_id)

        else:
            if 'stream_id' in kwargs and kwargs['stream_id']:
                # Download the stream
                stream_id = kwargs['stream_id']
            else:
                # Download stream with the best quality
                from .processor.ffmpeg import has_ffmpeg_installed
                if has_ffmpeg_installed() and player is None and self.dash_streams or not self.streams_sorted:
                    #stream_id = list(self.dash_streams)[-1]
                    itags = sorted(self.dash_streams,
                                   key=lambda i: -self.dash_streams[i]['size'])
                    stream_id = itags[0]
                else:
                    stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else self.streams_sorted[0]['itag']

            if 'index' not in kwargs:
                self.p(stream_id)
            else:
                self.p_i(stream_id)

            if stream_id in self.streams:
                urls = self.streams[stream_id]['src']
                ext = self.streams[stream_id]['container']
                total_size = self.streams[stream_id]['size']
            else:
                urls = self.dash_streams[stream_id]['src']
                ext = self.dash_streams[stream_id]['container']
                total_size = self.dash_streams[stream_id]['size']

            if ext == 'm3u8' or ext == 'm4a':
                ext = 'mp4'

            if not urls:
                log.wtf('[Failed] Cannot extract video source.')
            # For legacy main()
            headers = {}
            if self.ua is not None:
                headers['User-Agent'] = self.ua
            if self.referer is not None:
                headers['Referer'] = self.referer
            download_urls(urls, self.title, ext, total_size, headers=headers,
                          output_dir=kwargs['output_dir'],
                          merge=kwargs['merge'],
                          av=stream_id in self.dash_streams,
                          vid=self.vid)

            if 'caption' not in kwargs or not kwargs['caption']:
                print('Skipping captions or danmaku.')
                return

            for lang in self.caption_tracks:
                filename = '%s.%s.srt' % (get_filename(self.title), lang)
                print('Saving %s ... ' % filename, end="", flush=True)
                srt = self.caption_tracks[lang]
                with open(os.path.join(kwargs['output_dir'], filename),
                          'w', encoding='utf-8') as x:
                    x.write(srt)
                print('Done.')

            if self.danmaku is not None and not dry_run:
                filename = '{}.cmt.xml'.format(get_filename(self.title))
                print('Downloading {} ...\n'.format(filename))
                with open(os.path.join(kwargs['output_dir'], filename), 'w', encoding='utf8') as fp:
                    fp.write(self.danmaku)

            if self.lyrics is not None and not dry_run:
                filename = '{}.lrc'.format(get_filename(self.title))
                print('Downloading {} ...\n'.format(filename))
                with open(os.path.join(kwargs['output_dir'], filename), 'w', encoding='utf8') as fp:
                    fp.write(self.lyrics)

            # For main_dev()
            #download_urls(urls, self.title, self.streams[stream_id]['container'], self.streams[stream_id]['size'])
        keep_obj = kwargs.get('keep_obj', False)
        if not keep_obj:
            self.__init__()
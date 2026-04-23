def download(self, **kwargs):
        """Override the original one
        Ugly ugly dirty hack"""
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

            if not urls:
                log.wtf('[Failed] Cannot extract video source.')
            # For legacy main()

            #Here's the change!!
            # ffmpeg fails to parse.
            # download_url_ffmpeg(urls[0], self.title, 'mp4', output_dir=kwargs['output_dir'], merge=kwargs['merge'], stream=False)
            #Here's the way works out
            urls = general_m3u8_extractor(urls[0])
            # ffmpeg fail to convert the output video with mkv extension, due to sort of timestamp problem
            download_urls(urls, self.title, 'mp4', 0, **kwargs)

            if not kwargs['caption']:
                print('Skipping captions.')
                return
            for lang in self.caption_tracks:
                filename = '%s.%s.srt' % (get_filename(self.title), lang)
                print('Saving %s ... ' % filename, end="", flush=True)
                srt = self.caption_tracks[lang]
                with open(os.path.join(kwargs['output_dir'], filename),
                          'w', encoding='utf-8') as x:
                    x.write(srt)
                print('Done.')
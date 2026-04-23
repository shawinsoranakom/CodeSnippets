def prepare(self, **kwargs):
        self.ua = 'Mozilla/5.0 (iPad; CPU OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1,gzip(gfe)'

        assert self.url or self.vid

        if not self.vid and self.url:
            self.vid = self.__class__.get_vid_from_url(self.url)

            if self.vid is None:
                self.download_playlist_by_url(self.url, **kwargs)
                exit(0)

        if re.search(r'\Wlist=', self.url) and not kwargs.get('playlist'):
            log.w('This video is from a playlist. (use --playlist to download all videos in the playlist.)')

        # Extract from video page
        logging.debug('Extracting from the video page...')
        video_page = get_content('https://www.youtube.com/watch?v=%s' % self.vid, headers={'User-Agent': self.ua})

        try:
            jsUrl = re.search(r'([^"]*/base\.js)"', video_page).group(1)
        except:
            log.wtf('[Failed] Unable to find base.js on the video page')
        self.html5player = 'https://www.youtube.com' + jsUrl
        logging.debug('Retrieving the player code...')
        self.js = get_content(self.html5player).replace('\n', ' ')

        logging.debug('Loading ytInitialPlayerResponse...')
        ytInitialPlayerResponse = json.loads(re.search(r'ytInitialPlayerResponse\s*=\s*([^\n]+?});(\n|</script>|var )', video_page).group(1))
        self.check_playability_response(ytInitialPlayerResponse)

        # Get the video title
        self.title = ytInitialPlayerResponse["videoDetails"]["title"]

        # Check the status
        playabilityStatus = ytInitialPlayerResponse['playabilityStatus']
        status = playabilityStatus['status']
        logging.debug('status: %s' % status)
        if status != 'OK':
            # If cookies are loaded, status should be OK
            try:
                subreason = playabilityStatus['errorScreen']['playerErrorMessageRenderer']['subreason']['runs'][0]['text']
                log.e('[Error] %s (%s)' % (playabilityStatus['reason'], subreason))
            except:
                log.e('[Error] %s' % playabilityStatus['reason'])
            if status == 'LOGIN_REQUIRED':
                log.e('View the video from a browser and export the cookies, then use --cookies to load cookies.')
            exit(1)

        stream_list = ytInitialPlayerResponse['streamingData']['formats']

        for stream in stream_list:
            logging.debug('Found format: itag=%s' % stream['itag'])
            if 'signatureCipher' in stream:
                logging.debug('  Parsing signatureCipher for itag=%s...' % stream['itag'])
                qs = parse_qs(stream['signatureCipher'])
                #logging.debug(qs)
                sp = qs['sp'][0]
                sig = self.__class__.s_to_sig(self.js, qs['s'][0])
                url = qs['url'][0] + '&{}={}'.format(sp, sig)
            elif 'url' in stream:
                url = stream['url']
            else:
                log.wtf('  No signatureCipher or url for itag=%s' % stream['itag'])
            url = self.__class__.dethrottle(self.js, url)

            self.streams[str(stream['itag'])] = {
                'itag': str(stream['itag']),
                'url': url,
                'quality': stream['quality'],
                'type': stream['mimeType'],
                'mime': stream['mimeType'].split(';')[0],
                'container': mime_to_container(stream['mimeType'].split(';')[0]),
            }

        # FIXME: Prepare caption tracks
        try:
            caption_tracks = ytInitialPlayerResponse['captions']['playerCaptionsTracklistRenderer']['captionTracks']
            for ct in caption_tracks:
                ttsurl, lang = ct['baseUrl'], ct['languageCode']

                if ttsurl.startswith('/'):
                    ttsurl = 'https://www.youtube.com' + ttsurl
                tts_xml = parseString(get_content(ttsurl))
                transcript = tts_xml.getElementsByTagName('transcript')[0]
                texts = transcript.getElementsByTagName('text')
                srt = ""; seq = 0
                for text in texts:
                    if text.firstChild is None: continue # empty element
                    seq += 1
                    start = float(text.getAttribute('start'))
                    if text.getAttribute('dur'):
                        dur = float(text.getAttribute('dur'))
                    else: dur = 1.0 # could be ill-formed XML
                    finish = start + dur
                    m, s = divmod(start, 60); h, m = divmod(m, 60)
                    start = '{:0>2}:{:0>2}:{:06.3f}'.format(int(h), int(m), s).replace('.', ',')
                    m, s = divmod(finish, 60); h, m = divmod(m, 60)
                    finish = '{:0>2}:{:0>2}:{:06.3f}'.format(int(h), int(m), s).replace('.', ',')
                    content = unescape_html(text.firstChild.nodeValue)

                    srt += '%s\n' % str(seq)
                    srt += '%s --> %s\n' % (start, finish)
                    srt += '%s\n\n' % content

                if 'kind' in ct:
                    self.caption_tracks[ct['vssId']] = srt  # autogenerated
                else:
                    self.caption_tracks[lang] = srt
        except: pass

        # Prepare DASH streams
        if 'adaptiveFormats' in ytInitialPlayerResponse['streamingData']:
            streams = ytInitialPlayerResponse['streamingData']['adaptiveFormats']

            # FIXME: dead code?
            # streams without contentLength got broken urls, just remove them (#2767)
            streams = [stream for stream in streams if 'contentLength' in stream]

            for stream in streams:
                logging.debug('Found adaptiveFormat: itag=%s' % stream['itag'])
                stream['itag'] = str(stream['itag'])
                if 'qualityLabel' in stream:
                    stream['quality_label'] = stream['qualityLabel']
                    del stream['qualityLabel']
                    logging.debug('  quality_label: \t%s' % stream['quality_label'])
                if 'width' in stream:
                    stream['size'] = '{}x{}'.format(stream['width'], stream['height'])
                    del stream['width']
                    del stream['height']
                    logging.debug('  size: \t%s' % stream['size'])
                stream['type'] = stream['mimeType']
                logging.debug('  type: \t%s' % stream['type'])
                stream['clen'] = stream['contentLength']
                stream['init'] = '{}-{}'.format(
                    stream['initRange']['start'],
                    stream['initRange']['end'])
                stream['index'] = '{}-{}'.format(
                    stream['indexRange']['start'],
                    stream['indexRange']['end'])
                del stream['mimeType']
                del stream['contentLength']
                del stream['initRange']
                del stream['indexRange']

                if 'signatureCipher' in stream:
                    logging.debug('  Parsing signatureCipher for itag=%s...' % stream['itag'])
                    qs = parse_qs(stream['signatureCipher'])
                    #logging.debug(qs)
                    sp = qs['sp'][0]
                    sig = self.__class__.s_to_sig(self.js, qs['s'][0])
                    url = qs['url'][0] + '&ratebypass=yes&{}={}'.format(sp, sig)
                elif 'url' in stream:
                    url = stream['url']
                else:
                    log.wtf('No signatureCipher or url for itag=%s' % stream['itag'])
                url = self.__class__.dethrottle(self.js, url)
                stream['url'] = url

            for stream in streams: # audio
                if stream['type'].startswith('audio/mp4'):
                    dash_mp4_a_url = stream['url']
                    dash_mp4_a_size = stream['clen']
                elif stream['type'].startswith('audio/webm'):
                    dash_webm_a_url = stream['url']
                    dash_webm_a_size = stream['clen']
            for stream in streams: # video
                if 'size' in stream:
                    if stream['type'].startswith('video/mp4'):
                        mimeType = 'video/mp4'
                        dash_url = stream['url']
                        dash_size = stream['clen']
                        itag = stream['itag']
                        dash_urls = self.__class__.chunk_by_range(dash_url, int(dash_size))
                        dash_mp4_a_urls = self.__class__.chunk_by_range(dash_mp4_a_url, int(dash_mp4_a_size))
                        self.dash_streams[itag] = {
                            'quality': '%s (%s)' % (stream['size'], stream['quality_label']),
                            'itag': itag,
                            'type': mimeType,
                            'mime': mimeType,
                            'container': 'mp4',
                            'src': [dash_urls, dash_mp4_a_urls],
                            'size': int(dash_size) + int(dash_mp4_a_size)
                        }
                    elif stream['type'].startswith('video/webm'):
                        mimeType = 'video/webm'
                        dash_url = stream['url']
                        dash_size = stream['clen']
                        itag = stream['itag']
                        audio_url = None
                        audio_size = None
                        try:
                            audio_url = dash_webm_a_url
                            audio_size = int(dash_webm_a_size)
                        except UnboundLocalError as e:
                            audio_url = dash_mp4_a_url
                            audio_size = int(dash_mp4_a_size)
                        dash_urls = self.__class__.chunk_by_range(dash_url, int(dash_size))
                        audio_urls = self.__class__.chunk_by_range(audio_url, int(audio_size))
                        self.dash_streams[itag] = {
                            'quality': '%s (%s)' % (stream['size'], stream['quality_label']),
                            'itag': itag,
                            'type': mimeType,
                            'mime': mimeType,
                            'container': 'webm',
                            'src': [dash_urls, audio_urls],
                            'size': int(dash_size) + int(audio_size)
                        }
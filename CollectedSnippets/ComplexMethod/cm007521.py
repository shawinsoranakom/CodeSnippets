def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        account_id = mobj.group('account_id')

        # Handle http://video.arkena.com/play2/embed/player URL
        if not video_id:
            qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
            video_id = qs.get('mediaId', [None])[0]
            account_id = qs.get('accountId', [None])[0]
            if not video_id or not account_id:
                raise ExtractorError('Invalid URL', expected=True)

        media = self._download_json(
            'https://video.qbrick.com/api/v1/public/accounts/%s/medias/%s' % (account_id, video_id),
            video_id, query={
                # https://video.qbrick.com/docs/api/examples/library-api.html
                'fields': 'asset/resources/*/renditions/*(height,id,language,links/*(href,mimeType),type,size,videos/*(audios/*(codec,sampleRate),bitrate,codec,duration,height,width),width),created,metadata/*(title,description),tags',
            })
        metadata = media.get('metadata') or {}
        title = metadata['title']

        duration = None
        formats = []
        thumbnails = []
        subtitles = {}
        for resource in media['asset']['resources']:
            for rendition in (resource.get('renditions') or []):
                rendition_type = rendition.get('type')
                for i, link in enumerate(rendition.get('links') or []):
                    href = link.get('href')
                    if not href:
                        continue
                    if rendition_type == 'image':
                        thumbnails.append({
                            'filesize': int_or_none(rendition.get('size')),
                            'height': int_or_none(rendition.get('height')),
                            'id': rendition.get('id'),
                            'url': href,
                            'width': int_or_none(rendition.get('width')),
                        })
                    elif rendition_type == 'subtitle':
                        subtitles.setdefault(rendition.get('language') or 'en', []).append({
                            'url': href,
                        })
                    elif rendition_type == 'video':
                        f = {
                            'filesize': int_or_none(rendition.get('size')),
                            'format_id': rendition.get('id'),
                            'url': href,
                        }
                        video = try_get(rendition, lambda x: x['videos'][i], dict)
                        if video:
                            if not duration:
                                duration = float_or_none(video.get('duration'))
                            f.update({
                                'height': int_or_none(video.get('height')),
                                'tbr': int_or_none(video.get('bitrate'), 1000),
                                'vcodec': video.get('codec'),
                                'width': int_or_none(video.get('width')),
                            })
                            audio = try_get(video, lambda x: x['audios'][0], dict)
                            if audio:
                                f.update({
                                    'acodec': audio.get('codec'),
                                    'asr': int_or_none(audio.get('sampleRate')),
                                })
                        formats.append(f)
                    elif rendition_type == 'index':
                        mime_type = link.get('mimeType')
                        if mime_type == 'application/smil+xml':
                            formats.extend(self._extract_smil_formats(
                                href, video_id, fatal=False))
                        elif mime_type == 'application/x-mpegURL':
                            formats.extend(self._extract_m3u8_formats(
                                href, video_id, 'mp4', 'm3u8_native',
                                m3u8_id='hls', fatal=False))
                        elif mime_type == 'application/hds+xml':
                            formats.extend(self._extract_f4m_formats(
                                href, video_id, f4m_id='hds', fatal=False))
                        elif mime_type == 'application/dash+xml':
                            formats.extend(self._extract_f4m_formats(
                                href, video_id, f4m_id='hds', fatal=False))
                        elif mime_type == 'application/vnd.ms-sstr+xml':
                            formats.extend(self._extract_ism_formats(
                                href, video_id, ism_id='mss', fatal=False))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': metadata.get('description'),
            'timestamp': parse_iso8601(media.get('created')),
            'thumbnails': thumbnails,
            'subtitles': subtitles,
            'duration': duration,
            'tags': media.get('tags'),
            'formats': formats,
        }
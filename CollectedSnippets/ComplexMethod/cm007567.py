def _process_media_selector(self, media_selection, programme_id):
        formats = []
        subtitles = None
        urls = []

        for media in self._extract_medias(media_selection):
            kind = media.get('kind')
            if kind in ('video', 'audio'):
                bitrate = int_or_none(media.get('bitrate'))
                encoding = media.get('encoding')
                width = int_or_none(media.get('width'))
                height = int_or_none(media.get('height'))
                file_size = int_or_none(media.get('media_file_size'))
                for connection in self._extract_connections(media):
                    href = connection.get('href')
                    if href in urls:
                        continue
                    if href:
                        urls.append(href)
                    conn_kind = connection.get('kind')
                    protocol = connection.get('protocol')
                    supplier = connection.get('supplier')
                    transfer_format = connection.get('transferFormat')
                    format_id = supplier or conn_kind or protocol
                    # ASX playlist
                    if supplier == 'asx':
                        for i, ref in enumerate(self._extract_asx_playlist(connection, programme_id)):
                            formats.append({
                                'url': ref,
                                'format_id': 'ref%s_%s' % (i, format_id),
                            })
                    elif transfer_format == 'dash':
                        formats.extend(self._extract_mpd_formats(
                            href, programme_id, mpd_id=format_id, fatal=False))
                    elif transfer_format == 'hls':
                        # TODO: let expected_status be passed into _extract_xxx_formats() instead
                        try:
                            fmts = self._extract_m3u8_formats(
                                href, programme_id, ext='mp4', entry_protocol='m3u8_native',
                                m3u8_id=format_id, fatal=False)
                        except ExtractorError as e:
                            if not (isinstance(e.exc_info[1], compat_urllib_error.HTTPError)
                                    and e.exc_info[1].code in (403, 404)):
                                raise
                            fmts = []
                        formats.extend(fmts)
                    elif transfer_format == 'hds':
                        formats.extend(self._extract_f4m_formats(
                            href, programme_id, f4m_id=format_id, fatal=False))
                    else:
                        if not supplier and bitrate:
                            format_id += '-%d' % bitrate
                        fmt = {
                            'format_id': format_id,
                            'filesize': file_size,
                        }
                        if kind == 'video':
                            fmt.update({
                                'width': width,
                                'height': height,
                                'tbr': bitrate,
                                'vcodec': encoding,
                            })
                        else:
                            fmt.update({
                                'abr': bitrate,
                                'acodec': encoding,
                                'vcodec': 'none',
                            })
                        if protocol in ('http', 'https'):
                            # Direct link
                            fmt.update({
                                'url': href,
                            })
                        elif protocol == 'rtmp':
                            application = connection.get('application', 'ondemand')
                            auth_string = connection.get('authString')
                            identifier = connection.get('identifier')
                            server = connection.get('server')
                            fmt.update({
                                'url': '%s://%s/%s?%s' % (protocol, server, application, auth_string),
                                'play_path': identifier,
                                'app': '%s?%s' % (application, auth_string),
                                'page_url': 'http://www.bbc.co.uk',
                                'player_url': 'http://www.bbc.co.uk/emp/releases/iplayer/revisions/617463_618125_4/617463_618125_4_emp.swf',
                                'rtmp_live': False,
                                'ext': 'flv',
                            })
                        else:
                            continue
                        formats.append(fmt)
            elif kind == 'captions':
                subtitles = self.extract_subtitles(media, programme_id)
        return formats, subtitles
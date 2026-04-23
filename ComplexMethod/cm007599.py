def _parse_f4m_formats(self, manifest, manifest_url, video_id, preference=None, f4m_id=None,
                           transform_source=lambda s: fix_xml_ampersands(s).strip(),
                           fatal=True, m3u8_id=None):
        if not isinstance(manifest, compat_etree_Element) and not fatal:
            return []

        # currently youtube-dl cannot decode the playerVerificationChallenge as Akamai uses Adobe Alchemy
        akamai_pv = manifest.find('{http://ns.adobe.com/f4m/1.0}pv-2.0')
        if akamai_pv is not None and ';' in akamai_pv.text:
            playerVerificationChallenge = akamai_pv.text.split(';')[0]
            if playerVerificationChallenge.strip() != '':
                return []

        formats = []
        manifest_version = '1.0'
        media_nodes = manifest.findall('{http://ns.adobe.com/f4m/1.0}media')
        if not media_nodes:
            manifest_version = '2.0'
            media_nodes = manifest.findall('{http://ns.adobe.com/f4m/2.0}media')
        # Remove unsupported DRM protected media from final formats
        # rendition (see https://github.com/ytdl-org/youtube-dl/issues/8573).
        media_nodes = remove_encrypted_media(media_nodes)
        if not media_nodes:
            return formats

        manifest_base_url = get_base_url(manifest)

        bootstrap_info = xpath_element(
            manifest, ['{http://ns.adobe.com/f4m/1.0}bootstrapInfo', '{http://ns.adobe.com/f4m/2.0}bootstrapInfo'],
            'bootstrap info', default=None)

        vcodec = None
        mime_type = xpath_text(
            manifest, ['{http://ns.adobe.com/f4m/1.0}mimeType', '{http://ns.adobe.com/f4m/2.0}mimeType'],
            'base URL', default=None)
        if mime_type and mime_type.startswith('audio/'):
            vcodec = 'none'

        for i, media_el in enumerate(media_nodes):
            tbr = int_or_none(media_el.attrib.get('bitrate'))
            width = int_or_none(media_el.attrib.get('width'))
            height = int_or_none(media_el.attrib.get('height'))
            format_id = '-'.join(filter(None, [f4m_id, compat_str(i if tbr is None else tbr)]))
            # If <bootstrapInfo> is present, the specified f4m is a
            # stream-level manifest, and only set-level manifests may refer to
            # external resources.  See section 11.4 and section 4 of F4M spec
            if bootstrap_info is None:
                media_url = None
                # @href is introduced in 2.0, see section 11.6 of F4M spec
                if manifest_version == '2.0':
                    media_url = media_el.attrib.get('href')
                if media_url is None:
                    media_url = media_el.attrib.get('url')
                if not media_url:
                    continue
                manifest_url = (
                    media_url if media_url.startswith('http://') or media_url.startswith('https://')
                    else ((manifest_base_url or '/'.join(manifest_url.split('/')[:-1])) + '/' + media_url))
                # If media_url is itself a f4m manifest do the recursive extraction
                # since bitrates in parent manifest (this one) and media_url manifest
                # may differ leading to inability to resolve the format by requested
                # bitrate in f4m downloader
                ext = determine_ext(manifest_url)
                if ext == 'f4m':
                    f4m_formats = self._extract_f4m_formats(
                        manifest_url, video_id, preference=preference, f4m_id=f4m_id,
                        transform_source=transform_source, fatal=fatal)
                    # Sometimes stream-level manifest contains single media entry that
                    # does not contain any quality metadata (e.g. http://matchtv.ru/#live-player).
                    # At the same time parent's media entry in set-level manifest may
                    # contain it. We will copy it from parent in such cases.
                    if len(f4m_formats) == 1:
                        f = f4m_formats[0]
                        f.update({
                            'tbr': f.get('tbr') or tbr,
                            'width': f.get('width') or width,
                            'height': f.get('height') or height,
                            'format_id': f.get('format_id') if not tbr else format_id,
                            'vcodec': vcodec,
                        })
                    formats.extend(f4m_formats)
                    continue
                elif ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        manifest_url, video_id, 'mp4', preference=preference,
                        m3u8_id=m3u8_id, fatal=fatal))
                    continue
            formats.append({
                'format_id': format_id,
                'url': manifest_url,
                'manifest_url': manifest_url,
                'ext': 'flv' if bootstrap_info is not None else None,
                'protocol': 'f4m',
                'tbr': tbr,
                'width': width,
                'height': height,
                'vcodec': vcodec,
                'preference': preference,
            })
        return formats
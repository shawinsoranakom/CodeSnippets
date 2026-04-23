def real_download(self, filename, info_dict):
        man_url = info_dict['url']
        requested_bitrate = info_dict.get('tbr')
        self.to_screen('[%s] Downloading f4m manifest' % self.FD_NAME)

        urlh = self.ydl.urlopen(self._prepare_url(info_dict, man_url))
        man_url = urlh.geturl()
        # Some manifests may be malformed, e.g. prosiebensat1 generated manifests
        # (see https://github.com/ytdl-org/youtube-dl/issues/6215#issuecomment-121704244
        # and https://github.com/ytdl-org/youtube-dl/issues/7823)
        manifest = fix_xml_ampersands(urlh.read().decode('utf-8', 'ignore')).strip()

        doc = compat_etree_fromstring(manifest)
        formats = [(int(f.attrib.get('bitrate', -1)), f)
                   for f in self._get_unencrypted_media(doc)]
        if requested_bitrate is None or len(formats) == 1:
            # get the best format
            formats = sorted(formats, key=lambda f: f[0])
            rate, media = formats[-1]
        else:
            rate, media = list(filter(
                lambda f: int(f[0]) == requested_bitrate, formats))[0]

        # Prefer baseURL for relative URLs as per 11.2 of F4M 3.0 spec.
        man_base_url = get_base_url(doc) or man_url

        base_url = compat_urlparse.urljoin(man_base_url, media.attrib['url'])
        bootstrap_node = doc.find(_add_ns('bootstrapInfo'))
        boot_info, bootstrap_url = self._parse_bootstrap_node(
            bootstrap_node, man_base_url)
        live = boot_info['live']
        metadata_node = media.find(_add_ns('metadata'))
        if metadata_node is not None:
            metadata = compat_b64decode(metadata_node.text)
        else:
            metadata = None

        fragments_list = build_fragments_list(boot_info)
        test = self.params.get('test', False)
        if test:
            # We only download the first fragment
            fragments_list = fragments_list[:1]
        total_frags = len(fragments_list)
        # For some akamai manifests we'll need to add a query to the fragment url
        akamai_pv = xpath_text(doc, _add_ns('pv-2.0'))

        ctx = {
            'filename': filename,
            'total_frags': total_frags,
            'live': live,
        }

        self._prepare_frag_download(ctx)

        dest_stream = ctx['dest_stream']

        if ctx['complete_frags_downloaded_bytes'] == 0:
            write_flv_header(dest_stream)
            if not live:
                write_metadata_tag(dest_stream, metadata)

        base_url_parsed = compat_urllib_parse_urlparse(base_url)

        self._start_frag_download(ctx)

        frag_index = 0
        while fragments_list:
            seg_i, frag_i = fragments_list.pop(0)
            frag_index += 1
            if frag_index <= ctx['fragment_index']:
                continue
            name = 'Seg%d-Frag%d' % (seg_i, frag_i)
            query = []
            if base_url_parsed.query:
                query.append(base_url_parsed.query)
            if akamai_pv:
                query.append(akamai_pv.strip(';'))
            if info_dict.get('extra_param_to_segment_url'):
                query.append(info_dict['extra_param_to_segment_url'])
            url_parsed = base_url_parsed._replace(path=base_url_parsed.path + name, query='&'.join(query))
            try:
                success, down_data = self._download_fragment(ctx, url_parsed.geturl(), info_dict)
                if not success:
                    return False
                reader = FlvReader(down_data)
                while True:
                    try:
                        _, box_type, box_data = reader.read_box_info()
                    except DataTruncatedError:
                        if test:
                            # In tests, segments may be truncated, and thus
                            # FlvReader may not be able to parse the whole
                            # chunk. If so, write the segment as is
                            # See https://github.com/ytdl-org/youtube-dl/issues/9214
                            dest_stream.write(down_data)
                            break
                        raise
                    if box_type == b'mdat':
                        self._append_fragment(ctx, box_data)
                        break
            except (compat_urllib_error.HTTPError, ) as err:
                if live and (err.code == 404 or err.code == 410):
                    # We didn't keep up with the live window. Continue
                    # with the next available fragment.
                    msg = 'Fragment %d unavailable' % frag_i
                    self.report_warning(msg)
                    fragments_list = []
                else:
                    raise

            if not fragments_list and not test and live and bootstrap_url:
                fragments_list = self._update_live_fragments(bootstrap_url, frag_i)
                total_frags += len(fragments_list)
                if fragments_list and (fragments_list[0][1] > frag_i + 1):
                    msg = 'Missed %d fragments' % (fragments_list[0][1] - (frag_i + 1))
                    self.report_warning(msg)

        self._finish_frag_download(ctx)

        return True
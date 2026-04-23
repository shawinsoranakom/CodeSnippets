def process_https_formats():
                proto = 'https'
                https_fmts = []

                for fmt_stream in streaming_formats:
                    # Live adaptive https formats are not supported: skip unless extractor-arg given
                    if fmt_stream.get('targetDurationSec') and skip_bad_formats:
                        continue

                    # FORMAT_STREAM_TYPE_OTF(otf=1) requires downloading the init fragment
                    # (adding `&sq=0` to the URL) and parsing emsg box to determine the
                    # number of fragment that would subsequently requested with (`&sq=N`)
                    if fmt_stream.get('type') == 'FORMAT_STREAM_TYPE_OTF' and not bool(fmt_stream.get('drmFamilies')):
                        continue

                    stream_id = get_stream_id(fmt_stream)
                    if not all_formats:
                        if stream_id in stream_ids:
                            continue

                    pot_policy: GvsPoTokenPolicy = self._get_default_ytcfg(client_name)['GVS_PO_TOKEN_POLICY'][StreamingProtocol.HTTPS]

                    require_po_token = (
                        stream_id[0] not in ['18']
                        and gvs_pot_required(pot_policy, is_premium_subscriber, player_token_provided))

                    po_token = (
                        gvs_pots.get(client_name)
                        or fetch_po_token_func(required=require_po_token or pot_policy.recommended))
                    if po_token:
                        if client_name not in gvs_pots:
                            gvs_pots[client_name] = po_token

                    fmt_url = fmt_stream.get('url')
                    encrypted_sig, sc = None, None
                    if not fmt_url:
                        # We still need to register original/default language information
                        # See: https://github.com/yt-dlp/yt-dlp/issues/14883
                        get_language_code_and_preference(fmt_stream)
                        sc = urllib.parse.parse_qs(fmt_stream.get('signatureCipher'))
                        fmt_url = traverse_obj(sc, ('url', 0, {url_or_none}))
                        encrypted_sig = traverse_obj(sc, ('s', 0))
                        if not all((sc, fmt_url, skip_player_js or player_url, encrypted_sig)):
                            msg_tmpl = (
                                '{}Some {} client https formats have been skipped as they are missing a URL. '
                                '{}. See  https://github.com/yt-dlp/yt-dlp/issues/12482  for more details')
                            if client_name in ('web', 'web_safari'):
                                self.write_debug(msg_tmpl.format(
                                    f'{video_id}: ', client_name,
                                    'YouTube is forcing SABR streaming for this client'), only_once=True)
                            else:
                                msg = (
                                    f'YouTube may have enabled the SABR-only streaming experiment for '
                                    f'{"your account" if self.is_authenticated else "the current session"}')
                                self.report_warning(msg_tmpl.format('', client_name, msg), video_id, only_once=True)
                            continue

                    fmt = process_format_stream(
                        fmt_stream, proto, missing_pot=require_po_token and not po_token,
                        super_resolution=is_super_resolution(fmt_url))
                    if not fmt:
                        continue

                    # signature
                    if encrypted_sig:
                        if skip_player_js:
                            continue
                        solve_js_challenges()
                        spec = self._load_player_data_from_cache(
                            'sigfuncs', player_url, len(encrypted_sig), use_disk_cache=True)
                        if not spec:
                            continue
                        fmt_url += '&{}={}'.format(
                            traverse_obj(sc, ('sp', -1)) or 'signature',
                            solve_sig(encrypted_sig, spec))

                    # n challenge
                    query = parse_qs(fmt_url)
                    if query.get('n'):
                        if skip_player_js:
                            continue
                        n_challenge = query['n'][0]
                        solve_js_challenges()
                        n_result = self._load_player_data_from_cache('n', player_url, n_challenge)
                        if not n_result:
                            continue
                        fmt_url = update_url_query(fmt_url, {'n': n_result})

                    if po_token:
                        fmt_url = update_url_query(fmt_url, {'pot': po_token})

                    fmt['url'] = fmt_url

                    if stream_id[0]:
                        itags[stream_id[0]].add((proto, fmt.get('language')))
                        stream_ids.append(stream_id)

                    # For handling potential pre-playback required waiting period
                    if live_status not in ('is_live', 'post_live'):
                        fmt['available_at'] = available_at

                    https_fmts.append(fmt)

                for fmt in https_fmts:
                    if (all_formats or 'dashy' in format_types) and fmt['filesize']:
                        yield {
                            **fmt,
                            'format_id': f'{fmt["format_id"]}-dashy' if all_formats else fmt['format_id'],
                            'protocol': 'http_dash_segments',
                            'fragments': build_fragments(fmt),
                        }
                    if all_formats or 'dashy' not in format_types:
                        fmt['downloader_options'] = {'http_chunk_size': CHUNK_SIZE}
                        yield fmt
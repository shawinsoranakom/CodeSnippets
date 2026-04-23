def _extract_player_responses(self, clients, video_id, webpage, webpage_client, webpage_ytcfg, is_premium_subscriber):
        initial_pr = None
        if webpage:
            initial_pr = self._search_json(
                self._YT_INITIAL_PLAYER_RESPONSE_RE, webpage,
                f'{webpage_client} client initial player response', video_id, fatal=False)

        prs = []
        deprioritized_prs = []

        if initial_pr and not self._invalid_player_response(initial_pr, video_id):
            # Android player_response does not have microFormats which are needed for
            # extraction of some data. So we return the initial_pr with formats
            # stripped out even if not requested by the user
            # See: https://github.com/yt-dlp/yt-dlp/issues/501
            prs.append({**initial_pr, 'streamingData': None})

        all_clients = set(clients)
        clients = clients[::-1]

        def append_client(*client_names):
            """ Append the first client name that exists but not already used """
            for client_name in client_names:
                actual_client = _split_innertube_client(client_name)[0]
                if actual_client in INNERTUBE_CLIENTS:
                    if actual_client not in all_clients:
                        clients.append(client_name)
                        all_clients.add(actual_client)
                        return

        tried_iframe_fallback = False
        player_url = visitor_data = data_sync_id = None
        skipped_clients = {}
        while clients:
            deprioritize_pr = False
            client, base_client, variant = _split_innertube_client(clients.pop())
            player_ytcfg = webpage_ytcfg if client == webpage_client else {}
            if 'configs' not in self._configuration_arg('player_skip') and client != webpage_client:
                player_ytcfg = self._download_ytcfg(client, video_id) or player_ytcfg

            player_url = player_url or self._extract_player_url(webpage_ytcfg, player_ytcfg, webpage=webpage)
            require_js_player = self._get_default_ytcfg(client).get('REQUIRE_JS_PLAYER')
            if 'js' in self._configuration_arg('player_skip'):
                require_js_player = False
                player_url = None

            if not player_url and not tried_iframe_fallback and require_js_player:
                player_url = self._download_player_url(video_id)
                tried_iframe_fallback = True

            pr = None
            if client == webpage_client and 'player_response' not in self._skipped_webpage_data:
                pr = initial_pr

            visitor_data = visitor_data or self._extract_visitor_data(webpage_ytcfg, initial_pr, player_ytcfg)
            data_sync_id = data_sync_id or self._extract_data_sync_id(webpage_ytcfg, initial_pr, player_ytcfg)

            fetch_po_token_args = {
                'client': client,
                'visitor_data': visitor_data,
                'video_id': video_id,
                'data_sync_id': data_sync_id if self.is_authenticated else None,
                'player_url': player_url if require_js_player else None,
                'webpage': webpage,
                'session_index': self._extract_session_index(webpage_ytcfg, player_ytcfg),
                'ytcfg': player_ytcfg or self._get_default_ytcfg(client),
            }

            # Don't need a player PO token for WEB if using player response from webpage
            player_pot_policy: PlayerPoTokenPolicy = self._get_default_ytcfg(client)['PLAYER_PO_TOKEN_POLICY']
            player_po_token = None if pr else self.fetch_po_token(
                context=_PoTokenContext.PLAYER, **fetch_po_token_args,
                required=player_pot_policy.required or player_pot_policy.recommended)

            fetch_gvs_po_token_func = functools.partial(
                self.fetch_po_token, context=_PoTokenContext.GVS, **fetch_po_token_args)

            fetch_subs_po_token_func = functools.partial(
                self.fetch_po_token, context=_PoTokenContext.SUBS, **fetch_po_token_args)

            try:
                pr = pr or self._extract_player_response(
                    client, video_id,
                    webpage_ytcfg=player_ytcfg or webpage_ytcfg,
                    player_ytcfg=player_ytcfg,
                    player_url=player_url,
                    initial_pr=initial_pr,
                    visitor_data=visitor_data,
                    data_sync_id=data_sync_id,
                    po_token=player_po_token)
            except ExtractorError as e:
                self.report_warning(e)
                continue

            if pr_id := self._invalid_player_response(pr, video_id):
                skipped_clients[client] = pr_id
            elif pr:
                # Save client details for introspection later
                innertube_context = traverse_obj(player_ytcfg or self._get_default_ytcfg(client), 'INNERTUBE_CONTEXT')
                sd = pr.setdefault('streamingData', {})
                sd[STREAMING_DATA_CLIENT_NAME] = client
                sd[STREAMING_DATA_FETCH_GVS_PO_TOKEN] = fetch_gvs_po_token_func
                sd[STREAMING_DATA_PLAYER_TOKEN_PROVIDED] = bool(player_po_token)
                sd[STREAMING_DATA_INNERTUBE_CONTEXT] = innertube_context
                sd[STREAMING_DATA_FETCH_SUBS_PO_TOKEN] = fetch_subs_po_token_func
                sd[STREAMING_DATA_IS_PREMIUM_SUBSCRIBER] = is_premium_subscriber
                sd[STREAMING_DATA_AVAILABLE_AT_TIMESTAMP] = self._get_available_at_timestamp(pr, video_id, client)
                for f in traverse_obj(sd, (('formats', 'adaptiveFormats'), ..., {dict})):
                    f[STREAMING_DATA_CLIENT_NAME] = client
                    f[STREAMING_DATA_FETCH_GVS_PO_TOKEN] = fetch_gvs_po_token_func
                    f[STREAMING_DATA_IS_PREMIUM_SUBSCRIBER] = is_premium_subscriber
                    f[STREAMING_DATA_PLAYER_TOKEN_PROVIDED] = bool(player_po_token)
                if deprioritize_pr:
                    deprioritized_prs.append(pr)
                else:
                    prs.append(pr)

            if (
                # Is this a "made for kids" video that can't be downloaded with android_vr?
                client == 'android_vr' and self._is_unplayable(pr)
                and webpage and 'made for kids' in webpage
                # ...and is a JS runtime is available?
                and any(p.is_available() for p in self._jsc_director.providers.values())
            ):
                append_client('web_embedded')

            # web_embedded can work around age-gate and age-verification for some embeddable videos
            if self._is_agegated(pr) and variant != 'web_embedded':
                append_client(f'web_embedded.{base_client}')
            # Unauthenticated users will only get web_embedded client formats if age-gated
            if self._is_agegated(pr) and not self.is_authenticated:
                self.to_screen(
                    f'{video_id}: This video is age-restricted; some formats may be missing '
                    f'without authentication. {self._youtube_login_hint}', only_once=True)

            # EU countries require age-verification for accounts to access age-restricted videos
            # If account is not age-verified, _is_agegated() will be truthy for non-embedded clients
            embedding_is_disabled = variant == 'web_embedded' and self._is_unplayable(pr)
            if self.is_authenticated and (self._is_agegated(pr) or embedding_is_disabled):
                self.to_screen(
                    f'{video_id}: This video is age-restricted and YouTube is requiring '
                    'account age-verification; some formats may be missing', only_once=True)
                # web_creator may work around age-verification for all videos but requires PO token
                append_client('web_creator')

            status = traverse_obj(pr, ('playabilityStatus', 'status', {str}))
            if status not in ('OK', 'LIVE_STREAM_OFFLINE', 'AGE_CHECK_REQUIRED', 'AGE_VERIFICATION_REQUIRED'):
                self.write_debug(f'{video_id}: {client} player response playability status: {status}')

        prs.extend(deprioritized_prs)

        if skipped_clients:
            self.report_warning(
                f'Skipping player responses from {"/".join(skipped_clients)} clients '
                f'(got player responses for video "{"/".join(set(skipped_clients.values()))}" instead of "{video_id}")')
            if not prs:
                raise ExtractorError(
                    'All player responses are invalid. Your IP is likely being blocked by Youtube', expected=True)
        elif not prs:
            raise ExtractorError('Failed to extract any player response')
        return prs, player_url
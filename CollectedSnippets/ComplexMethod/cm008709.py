def fetch_po_token(self, client='web', context: _PoTokenContext = _PoTokenContext.GVS, ytcfg=None, visitor_data=None,
                       data_sync_id=None, session_index=None, player_url=None, video_id=None, webpage=None,
                       required=False, **kwargs):
        """
        Fetch a PO Token for a given client and context. This function will validate required parameters for a given context and client.

        EXPERIMENTAL: This method is unstable and may change or be removed without notice.

        @param client: The client to fetch the PO Token for.
        @param context: The context in which the PO Token is used.
        @param ytcfg: The ytcfg for the client.
        @param visitor_data: visitor data.
        @param data_sync_id: data sync ID.
        @param session_index: session index.
        @param player_url: player URL.
        @param video_id: video ID.
        @param webpage: video webpage.
        @param required: Whether the PO Token is required (i.e. try to fetch unless policy is "never").
        @param kwargs: Additional arguments to pass down. May be more added in the future.
        @return: The fetched PO Token. None if it could not be fetched.
        """

        # TODO(future): This validation should be moved into pot framework.
        #  Some sort of middleware or validation provider perhaps?

        gvs_bind_to_video_id = False
        experiments = traverse_obj(ytcfg, (
            'WEB_PLAYER_CONTEXT_CONFIGS', ..., 'serializedExperimentFlags', {urllib.parse.parse_qs}))
        if 'true' in traverse_obj(experiments, (..., 'html5_generate_content_po_token', -1)):
            self.write_debug(
                f'{video_id}: Detected experiment to bind GVS PO Token '
                f'to video ID for {client} client', only_once=True)
            gvs_bind_to_video_id = True

        # GVS WebPO Token is bound to visitor_data / Visitor ID when logged out.
        # Must have visitor_data for it to function.
        if (
            player_url and context == _PoTokenContext.GVS
            and not visitor_data and not self.is_authenticated and not gvs_bind_to_video_id
        ):
            self.report_warning(
                f'Unable to fetch GVS PO Token for {client} client: Missing required Visitor Data. '
                f'You may need to pass Visitor Data with --extractor-args "youtube:visitor_data=XXX"', only_once=True)
            return

        if context == _PoTokenContext.PLAYER and not video_id:
            self.report_warning(
                f'Unable to fetch Player PO Token for {client} client: Missing required Video ID')
            return

        config_po_token = self._get_config_po_token(client, context)
        if config_po_token:
            # GVS WebPO token is bound to data_sync_id / account Session ID when logged in.
            if (
                player_url and context == _PoTokenContext.GVS
                and not data_sync_id and self.is_authenticated and not gvs_bind_to_video_id
            ):
                self.report_warning(
                    f'Got a GVS PO Token for {client} client, but missing Data Sync ID for account. Formats may not work.'
                    f'You may need to pass a Data Sync ID with --extractor-args "youtube:data_sync_id=XXX"')

            self.write_debug(f'{video_id}: Retrieved a {context.value} PO Token for {client} client from config')
            return config_po_token

        # Require GVS WebPO Token if logged in for external fetching
        if player_url and context == _PoTokenContext.GVS and not data_sync_id and self.is_authenticated:
            self.report_warning(
                f'Unable to fetch GVS PO Token for {client} client: Missing required Data Sync ID for account. '
                f'You may need to pass a Data Sync ID with --extractor-args "youtube:data_sync_id=XXX"', only_once=True)
            return

        po_token = self._fetch_po_token(
            client=client,
            context=context.value,
            ytcfg=ytcfg,
            visitor_data=visitor_data,
            data_sync_id=data_sync_id,
            session_index=session_index,
            player_url=player_url,
            video_id=video_id,
            video_webpage=webpage,
            required=required,
            _gvs_bind_to_video_id=gvs_bind_to_video_id,
            **kwargs,
        )

        if po_token:
            self.write_debug(f'{video_id}: Retrieved a {context.value} PO Token for {client} client')
            return po_token
def _extract_player_response(self, client, video_id, webpage_ytcfg, player_ytcfg, player_url, initial_pr, visitor_data, data_sync_id, po_token):
        headers = self.generate_api_headers(
            ytcfg=player_ytcfg,
            default_client=client,
            visitor_data=visitor_data,
            session_index=self._extract_session_index(webpage_ytcfg, player_ytcfg),
            delegated_session_id=(
                self._parse_data_sync_id(data_sync_id)[0]
                or self._extract_delegated_session_id(webpage_ytcfg, initial_pr, player_ytcfg)
            ),
            user_session_id=(
                self._parse_data_sync_id(data_sync_id)[1]
                or self._extract_user_session_id(webpage_ytcfg, initial_pr, player_ytcfg)
            ),
        )

        yt_query = {
            'videoId': video_id,
        }

        default_pp = traverse_obj(
            INNERTUBE_CLIENTS, (_split_innertube_client(client)[0], 'PLAYER_PARAMS', {str}))
        if player_params := self._configuration_arg('player_params', [default_pp], casesense=True)[0]:
            yt_query['params'] = player_params

        if po_token:
            yt_query['serviceIntegrityDimensions'] = {'poToken': po_token}

        sts = self._extract_signature_timestamp(video_id, player_url, webpage_ytcfg, fatal=False) if player_url else None

        use_ad_playback_context = (
            self._configuration_arg('use_ad_playback_context', ['false'])[0] != 'false'
            and traverse_obj(INNERTUBE_CLIENTS, (client, 'SUPPORTS_AD_PLAYBACK_CONTEXT', {bool})))

        # web_embedded player requests may need to include encryptedHostFlags in its contentPlaybackContext.
        # This can be detected with the embeds_enable_encrypted_host_flags_enforcement experiemnt flag,
        # but there is no harm in including encryptedHostFlags with all web_embedded player requests.
        encrypted_context = None
        if _split_innertube_client(client)[2] == 'embedded':
            encrypted_context = traverse_obj(player_ytcfg, (
                'WEB_PLAYER_CONTEXT_CONFIGS', 'WEB_PLAYER_CONTEXT_CONFIG_ID_EMBEDDED_PLAYER', 'encryptedHostFlags'))

        yt_query.update(
            self._generate_player_context(
                sts=sts,
                use_ad_playback_context=use_ad_playback_context,
                encrypted_context=encrypted_context))

        return self._extract_response(
            item_id=video_id, ep='player', query=yt_query,
            ytcfg=player_ytcfg, headers=headers, fatal=True,
            default_client=client,
            note='Downloading {} player API JSON'.format(client.replace('_', ' ').strip()),
        ) or None
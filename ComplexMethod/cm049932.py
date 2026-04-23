def _join_sfu(self, ice_servers=None, force=False):
        if len(self.channel_id.rtc_session_ids) < SFU_MODE_THRESHOLD and not force:
            if self.channel_id.sfu_channel_uuid:
                self.channel_id.sfu_channel_uuid = None
                self.channel_id.sfu_server_url = None
            return
        elif self.channel_id.sfu_channel_uuid and self.channel_id.sfu_server_url:
            return
        sfu_server_url = discuss.get_sfu_url(self.env)
        if not sfu_server_url:
            return
        sfu_local_key = self.env["ir.config_parameter"].sudo().get_param("mail.sfu_local_key")
        if not sfu_local_key:
            sfu_local_key = str(uuid.uuid4())
            self.env["ir.config_parameter"].sudo().set_param("mail.sfu_local_key", sfu_local_key)
        json_web_token = jwt.sign(
            {"iss": f"{self.get_base_url()}:channel:{self.channel_id.id}", "key": sfu_local_key},
            key=discuss.get_sfu_key(self.env),
            ttl=30,
            algorithm=jwt.Algorithm.HS256,
        )
        try:
            response = requests.get(
                sfu_server_url + "/v1/channel",
                headers={"Authorization": "jwt " + json_web_token},
                timeout=3,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            _logger.warning("Failed to obtain a channel from the SFU server, user will stay in p2p: %s", error)
            return
        response_dict = response.json()
        self.channel_id.sfu_channel_uuid = response_dict["uuid"]
        self.channel_id.sfu_server_url = response_dict["url"]
        for session in self.channel_id.rtc_session_ids:
            session._bus_send(
                "discuss.channel.rtc.session/sfu_hot_swap",
                {"serverInfo": self._get_rtc_server_info(session, ice_servers, key=sfu_local_key)},
            )
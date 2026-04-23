async def get_data(self) -> PlaystationNetworkData:
        """Get title data from the PlayStation Network."""
        data = await self.hass.async_add_executor_job(self.retrieve_psn_data)
        data.username = self.user.online_id
        data.account_id = self.user.account_id
        data.shareable_profile_link = self.shareable_profile_link

        if "platform" in data.presence["basicPresence"]["primaryPlatformInfo"]:
            primary_platform = PlatformType(
                data.presence["basicPresence"]["primaryPlatformInfo"]["platform"]
            )
            game_title_info: dict[str, Any] = next(
                iter(
                    data.presence.get("basicPresence", {}).get("gameTitleInfoList", [])
                ),
                {},
            )
            status = data.presence.get("basicPresence", {}).get("primaryPlatformInfo")[
                "onlineStatus"
            ]
            title_format = (
                PlatformType(fmt) if (fmt := game_title_info.get("format")) else None
            )

            data.active_sessions[primary_platform] = SessionData(
                platform=primary_platform,
                status=status,
                title_id=game_title_info.get("npTitleId"),
                title_name=game_title_info.get("titleName"),
                format=title_format,
                media_image_url=(
                    game_title_info.get("conceptIconUrl")
                    or game_title_info.get("npTitleIconUrl")
                ),
            )

        if self.legacy_profile:
            presence = self.legacy_profile["profile"].get("presences", [])
            if (game_title_info := presence[0] if presence else {}) and game_title_info[
                "onlineStatus"
            ] != "offline":
                platform = PlatformType(game_title_info["platform"])

                if platform is PlatformType.PS4:
                    media_image_url = game_title_info.get("npTitleIconUrl")
                elif platform is PlatformType.PS3 and game_title_info.get("npTitleId"):
                    media_image_url = self.psn.game_title(
                        game_title_info["npTitleId"],
                        platform=PlatformType.PS3,
                        account_id="me",
                        np_communication_id="",
                    ).get_title_icon_url()
                elif platform is PlatformType.PS_VITA and game_title_info.get(
                    "npTitleId"
                ):
                    media_image_url = self.get_psvita_title_icon_url(game_title_info)
                else:
                    media_image_url = None

                data.active_sessions[platform] = SessionData(
                    platform=platform,
                    title_id=game_title_info.get("npTitleId"),
                    title_name=game_title_info.get("titleName"),
                    format=platform,
                    media_image_url=media_image_url,
                    status=game_title_info["onlineStatus"],
                )
        return data
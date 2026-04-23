async def _async_update_data(self) -> dict[str, TwitchUpdate]:
        await self.session.async_ensure_token_valid()
        await self.twitch.set_user_authentication(
            self.session.token["access_token"],
            OAUTH_SCOPES,
            self.session.token["refresh_token"],
            False,
        )
        data: dict[str, TwitchUpdate] = {}
        streams: dict[str, Stream] = {
            s.user_id: s
            async for s in self.twitch.get_followed_streams(
                user_id=self.current_user.id, first=100
            )
        }
        async for s in self.twitch.get_streams(user_id=[self.current_user.id]):
            streams.update({s.user_id: s})
        follows: dict[str, FollowedChannel] = {
            f.broadcaster_id: f
            async for f in await self.twitch.get_followed_channels(
                user_id=self.current_user.id, first=100
            )
        }
        for channel in self.users:
            followers = await self.twitch.get_channel_followers(channel.id)
            stream = streams.get(channel.id)
            follow = follows.get(channel.id)
            sub: UserSubscription | None = None
            try:
                sub = await self.twitch.check_user_subscription(
                    user_id=self.current_user.id, broadcaster_id=channel.id
                )
            except TwitchResourceNotFound:
                LOGGER.debug("User is not subscribed to %s", channel.display_name)
            except TwitchAPIException as exc:
                LOGGER.error("Error response on check_user_subscription: %s", exc)

            data[channel.id] = TwitchUpdate(
                channel.display_name,
                followers.total,
                bool(stream),
                stream.game_name if stream else None,
                stream.title if stream else None,
                stream.started_at if stream else None,
                stream.thumbnail_url.format(width="", height="") if stream else None,
                channel.profile_image_url,
                bool(sub),
                sub.is_gift if sub else None,
                {"1000": 1, "2000": 2, "3000": 3}.get(sub.tier) if sub else None,
                bool(follow),
                follow.followed_at if follow else None,
                stream.viewer_count if stream else None,
            )
        return data
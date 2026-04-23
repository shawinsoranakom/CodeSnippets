async def execute(self, command, data, params, challenge):
        """Execute a media command."""
        service_attrs = {ATTR_ENTITY_ID: self.state.entity_id}

        if command == COMMAND_MEDIA_SEEK_RELATIVE:
            service = media_player.SERVICE_MEDIA_SEEK

            rel_position = params["relativePositionMs"] / 1000
            seconds_since = 0  # Default to 0 seconds
            if self.state.state == STATE_PLAYING:
                now = dt_util.utcnow()
                upd_at = self.state.attributes.get(
                    media_player.ATTR_MEDIA_POSITION_UPDATED_AT, now
                )
                seconds_since = (now - upd_at).total_seconds()
            position = self.state.attributes.get(media_player.ATTR_MEDIA_POSITION, 0)
            max_position = self.state.attributes.get(
                media_player.ATTR_MEDIA_DURATION, 0
            )
            service_attrs[media_player.ATTR_MEDIA_SEEK_POSITION] = min(
                max(position + seconds_since + rel_position, 0), max_position
            )
        elif command == COMMAND_MEDIA_SEEK_TO_POSITION:
            service = media_player.SERVICE_MEDIA_SEEK

            max_position = self.state.attributes.get(
                media_player.ATTR_MEDIA_DURATION, 0
            )
            service_attrs[media_player.ATTR_MEDIA_SEEK_POSITION] = min(
                max(params["absPositionMs"] / 1000, 0), max_position
            )
        elif command == COMMAND_MEDIA_NEXT:
            service = media_player.SERVICE_MEDIA_NEXT_TRACK
        elif command == COMMAND_MEDIA_PAUSE:
            service = media_player.SERVICE_MEDIA_PAUSE
        elif command == COMMAND_MEDIA_PREVIOUS:
            service = media_player.SERVICE_MEDIA_PREVIOUS_TRACK
        elif command == COMMAND_MEDIA_RESUME:
            service = media_player.SERVICE_MEDIA_PLAY
        elif command == COMMAND_MEDIA_SHUFFLE:
            service = media_player.SERVICE_SHUFFLE_SET

            # Google Assistant only supports enabling shuffle
            service_attrs[media_player.ATTR_MEDIA_SHUFFLE] = True
        elif command == COMMAND_MEDIA_STOP:
            service = media_player.SERVICE_MEDIA_STOP
        else:
            raise SmartHomeError(ERR_NOT_SUPPORTED, "Command not supported")

        await self.hass.services.async_call(
            media_player.DOMAIN,
            service,
            service_attrs,
            blocking=not self.config.should_report_state,
            context=data.context,
        )
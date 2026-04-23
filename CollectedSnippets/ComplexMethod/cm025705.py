def send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to a user."""
        service_data = {ATTR_CHAT_ID: kwargs.get(ATTR_TARGET, self._chat_id)}
        data = kwargs.get(ATTR_DATA)

        # Set message tag
        if data is not None and ATTR_MESSAGE_TAG in data:
            message_tag = data.get(ATTR_MESSAGE_TAG)
            service_data.update({ATTR_MESSAGE_TAG: message_tag})

        # Set disable_notification
        if data is not None and ATTR_DISABLE_NOTIF in data:
            disable_notification = data.get(ATTR_DISABLE_NOTIF)
            service_data.update({ATTR_DISABLE_NOTIF: disable_notification})

        # Set parse_mode
        if data is not None and ATTR_PARSER in data:
            parse_mode = data.get(ATTR_PARSER)
            service_data.update({ATTR_PARSER: parse_mode})

        # Set disable_web_page_preview
        if data is not None and ATTR_DISABLE_WEB_PREV in data:
            disable_web_page_preview = data[ATTR_DISABLE_WEB_PREV]
            service_data.update({ATTR_DISABLE_WEB_PREV: disable_web_page_preview})

        # Set message_thread_id
        if data is not None and ATTR_MESSAGE_THREAD_ID in data:
            message_thread_id = data[ATTR_MESSAGE_THREAD_ID]
            service_data.update({ATTR_MESSAGE_THREAD_ID: message_thread_id})

        # Get keyboard info
        if data is not None and ATTR_KEYBOARD in data:
            keys = data.get(ATTR_KEYBOARD)
            keys = keys if isinstance(keys, list) else [keys]
            service_data.update(keyboard=keys)
        elif data is not None and ATTR_INLINE_KEYBOARD in data:
            keys = data.get(ATTR_INLINE_KEYBOARD)
            keys = keys if isinstance(keys, list) else [keys]
            service_data.update(inline_keyboard=keys)

        # Send a photo, video, document, voice, or location
        if data is not None and ATTR_PHOTO in data:
            photos = data.get(ATTR_PHOTO)
            photos = photos if isinstance(photos, list) else [photos]
            for photo_data in photos:
                service_data.update(photo_data)
                self.hass.services.call(
                    TELEGRAM_BOT_DOMAIN, "send_photo", service_data=service_data
                )
            return
        if data is not None and ATTR_VIDEO in data:
            videos = data.get(ATTR_VIDEO)
            videos = videos if isinstance(videos, list) else [videos]
            for video_data in videos:
                service_data.update(video_data)
                self.hass.services.call(
                    TELEGRAM_BOT_DOMAIN, "send_video", service_data=service_data
                )
            return
        if data is not None and ATTR_VOICE in data:
            voices = data.get(ATTR_VOICE)
            voices = voices if isinstance(voices, list) else [voices]
            for voice_data in voices:
                service_data.update(voice_data)
                self.hass.services.call(
                    TELEGRAM_BOT_DOMAIN, "send_voice", service_data=service_data
                )
            return
        if data is not None and ATTR_LOCATION in data:
            service_data.update(data.get(ATTR_LOCATION))
            self.hass.services.call(
                TELEGRAM_BOT_DOMAIN, "send_location", service_data=service_data
            )
            return
        if data is not None and ATTR_DOCUMENT in data:
            service_data.update(data.get(ATTR_DOCUMENT))
            self.hass.services.call(
                TELEGRAM_BOT_DOMAIN, "send_document", service_data=service_data
            )
            return

        # Send message

        if ATTR_TITLE in kwargs:
            service_data.update({ATTR_TITLE: kwargs.get(ATTR_TITLE)})
        if message:
            service_data.update({ATTR_MESSAGE: message})

        _LOGGER.debug(
            "TELEGRAM NOTIFIER calling %s.send_message with %s",
            TELEGRAM_BOT_DOMAIN,
            service_data,
        )
        self.hass.services.call(
            TELEGRAM_BOT_DOMAIN, "send_message", service_data=service_data
        )
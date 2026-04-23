def _get_msg_kwargs(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get parameters in message data kwargs."""

        def _make_row_inline_keyboard(row_keyboard: Any) -> list[InlineKeyboardButton]:
            """Make a list of InlineKeyboardButtons.

            It can accept:
              - a list of tuples like:
                `[(text_b1, data_callback_b1),
                (text_b2, data_callback_b2), ...]
              - a string like: `/cmd1, /cmd2, /cmd3`
              - or a string like: `text_b1:/cmd1, text_b2:/cmd2`
              - also supports urls instead of callback commands
            """
            buttons = []
            if isinstance(row_keyboard, str):
                for key in row_keyboard.split(","):
                    if ":/" in key:
                        # check if command or URL
                        if "https://" in key:
                            label = key.split(":")[0]
                            url = key[len(label) + 1 :]
                            buttons.append(InlineKeyboardButton(label, url=url))
                        else:
                            # commands like: 'Label:/cmd' become ('Label', '/cmd')
                            label = key.split(":/")[0]
                            command = key[len(label) + 1 :]
                            buttons.append(
                                InlineKeyboardButton(label, callback_data=command)
                            )
                    else:
                        # commands like: '/cmd' become ('CMD', '/cmd')
                        label = key.strip()[1:].upper()
                        buttons.append(InlineKeyboardButton(label, callback_data=key))
            elif isinstance(row_keyboard, list):
                for entry in row_keyboard:
                    text_btn, data_btn = entry
                    if data_btn.startswith("https://"):
                        buttons.append(InlineKeyboardButton(text_btn, url=data_btn))
                    else:
                        buttons.append(
                            InlineKeyboardButton(text_btn, callback_data=data_btn)
                        )
            else:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_inline_keyboard",
                )
            return buttons

        # Defaults
        params: dict[str, Any] = {
            ATTR_PARSER: self.parse_mode,
            ATTR_DISABLE_NOTIF: False,
            ATTR_DISABLE_WEB_PREV: None,
            ATTR_REPLY_TO_MSGID: None,
            ATTR_REPLYMARKUP: None,
            ATTR_TIMEOUT: None,
            ATTR_MESSAGE_TAG: None,
            ATTR_MESSAGE_THREAD_ID: None,
        }
        if data is not None:
            if ATTR_PARSER in data:
                params[ATTR_PARSER] = data[ATTR_PARSER]
            if ATTR_TIMEOUT in data:
                params[ATTR_TIMEOUT] = data[ATTR_TIMEOUT]
            if ATTR_DISABLE_NOTIF in data:
                params[ATTR_DISABLE_NOTIF] = data[ATTR_DISABLE_NOTIF]
            if ATTR_DISABLE_WEB_PREV in data:
                params[ATTR_DISABLE_WEB_PREV] = data[ATTR_DISABLE_WEB_PREV]
            if ATTR_REPLY_TO_MSGID in data:
                params[ATTR_REPLY_TO_MSGID] = data[ATTR_REPLY_TO_MSGID]
            if ATTR_MESSAGE_TAG in data:
                params[ATTR_MESSAGE_TAG] = data[ATTR_MESSAGE_TAG]
            if ATTR_MESSAGE_THREAD_ID in data:
                params[ATTR_MESSAGE_THREAD_ID] = data[ATTR_MESSAGE_THREAD_ID]
            # Keyboards:
            if ATTR_KEYBOARD in data:
                keys = data[ATTR_KEYBOARD]
                keys = keys if isinstance(keys, list) else [keys]
                if keys:
                    params[ATTR_REPLYMARKUP] = ReplyKeyboardMarkup(
                        [[key.strip() for key in row.split(",")] for row in keys],
                        resize_keyboard=data.get(ATTR_RESIZE_KEYBOARD, False),
                        one_time_keyboard=data.get(ATTR_ONE_TIME_KEYBOARD, False),
                    )
                else:
                    params[ATTR_REPLYMARKUP] = ReplyKeyboardRemove(True)

            elif ATTR_KEYBOARD_INLINE in data:
                keys = data.get(ATTR_KEYBOARD_INLINE)
                keys = keys if isinstance(keys, list) else [keys]
                params[ATTR_REPLYMARKUP] = InlineKeyboardMarkup(
                    [_make_row_inline_keyboard(row) for row in keys]
                )
        if params[ATTR_PARSER] == PARSER_PLAIN_TEXT:
            params[ATTR_PARSER] = None
        return params
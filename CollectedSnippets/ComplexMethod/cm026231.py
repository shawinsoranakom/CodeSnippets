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
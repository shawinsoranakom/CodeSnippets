def _get_answer(self, channel, body, values, command=False):
        odoobot = self.env.ref("base.partner_root")
        # onboarding
        odoobot_state = self.env.user.odoobot_state

        if channel.channel_type == "chat" and odoobot in channel.channel_member_ids.partner_id:
            # main flow
            source = _("Thanks")
            description = _("This is a temporary canned response to see how canned responses work.")
            if odoobot_state == 'onboarding_emoji' and self._body_contains_emoji(body):
                self.env.user.odoobot_state = "onboarding_command"
                self.env.user.odoobot_failed = False
                return self.env._(
                    "Great! 👍%(new_line)sTo access special commands, %(bold_start)sstart your "
                    "sentence with%(bold_end)s %(command_start)s/%(command_end)s. Try getting "
                    "help.",
                    **self._get_style_dict()
                )
            elif odoobot_state == 'onboarding_command' and command == 'help':
                self.env.user.odoobot_state = "onboarding_ping"
                self.env.user.odoobot_failed = False
                return self.env._(
                    "Wow you are a natural!%(new_line)sPing someone with @username to grab their "
                    "attention. %(bold_start)sTry to ping me using%(bold_end)s "
                    "%(command_start)s@OdooBot%(command_end)s in a sentence.",
                    **self._get_style_dict()
                )
            elif odoobot_state == "onboarding_ping" and odoobot.id in values.get("partner_ids", []):
                self.env.user.odoobot_state = "onboarding_attachement"
                self.env.user.odoobot_failed = False
                return self.env._(
                    "Yep, I am here! 🎉 %(new_line)sNow, try %(bold_start)ssending an "
                    "attachment%(bold_end)s, like a picture of your cute dog...",
                    **self._get_style_dict()
                )
            elif odoobot_state == "onboarding_attachement" and values.get("attachment_ids"):
                self.env["mail.canned.response"].create({
                    "source": source,
                    "substitution": _("Thanks for your feedback. Goodbye!"),
                })
                self.env.user.odoobot_failed = False
                self.env.user.odoobot_state = "onboarding_canned"
                return self.env._(
                    "Wonderful! 😇%(new_line)sTry typing %(command_start)s::%(command_end)s to use "
                    "canned responses. I've created a temporary one for you.",
                    **self._get_style_dict()
                )
            elif odoobot_state == "onboarding_canned" and self.env.context.get("canned_response_ids"):
                self.env["mail.canned.response"].search([
                    ("create_uid", "=", self.env.user.id),
                    ("source", "=", source),
                ]).unlink()
                self.env.user.odoobot_failed = False
                self.env.user.odoobot_state = "idle"
                return [
                    self.env._(
                        "Great! You can customize %(bold_start)scanned responses%(bold_end)s in the Discuss app.",
                        **self._get_style_dict(),
                    ),
                    self.env._(
                        "That’s the end of this overview. You can %(bold_start)sclose this conversation%(bold_end)s or type "
                        "%(command_start)sstart the tour%(command_end)s to see it again. Enjoy exploring Odoo!",
                        **self._get_style_dict(),
                    ),
                ]
            # repeat question if needed
            elif odoobot_state == 'onboarding_canned' and not self._is_help_requested(body):
                self.env.user.odoobot_failed = True
                return self.env._(
                    "Not sure what you are doing. Please, type %(command_start)s:%(command_end)s "
                    "and wait for the propositions. Select one of them and press enter.",
                    **self._get_style_dict()
                )
            elif odoobot_state in (False, "idle", "not_initialized") and (_('start the tour') in body.lower()):
                self.env.user.odoobot_state = "onboarding_emoji"
                return _("To start, try to send me an emoji :)")
            # easter eggs
            elif odoobot_state == "idle" and body in ['❤️', _('i love you'), _('love')]:
                return _("Aaaaaw that's really cute but, you know, bots don't work that way. You're too human for me! Let's keep it professional ❤️")
            elif _('fuck') in body or "fuck" in body:
                return _("That's not nice! I'm a bot but I have feelings... 💔")
            # help message
            elif self._is_help_requested(body) or odoobot_state == 'idle':
                return self.env._(
                    "Unfortunately, I'm just a bot 😞 I don't understand! If you need help "
                    "discovering our product, please check %(document_link_start)sour "
                    "documentation%(document_link_end)s or %(slides_link_start)sour "
                    "videos%(slides_link_end)s.",
                    **self._get_style_dict()
                )
            else:
                # repeat question
                if odoobot_state == 'onboarding_emoji':
                    self.env.user.odoobot_failed = True
                    return self.env._(
                        "Not exactly. To continue the tour, send an emoji:"
                        " %(bold_start)stype%(bold_end)s%(command_start)s :)%(command_end)s and "
                        "press enter.",
                        **self._get_style_dict()
                    )
                elif odoobot_state == 'onboarding_attachement':
                    self.env.user.odoobot_failed = True
                    return self.env._(
                        "To %(bold_start)ssend an attachment%(bold_end)s, click on the "
                        "%(paperclip_icon)s icon and select a file.",
                        **self._get_style_dict()
                    )
                elif odoobot_state == 'onboarding_command':
                    self.env.user.odoobot_failed = True
                    return self.env._(
                        "Not sure what you are doing. Please, type "
                        "%(command_start)s/%(command_end)s and wait for the propositions."
                        " Select %(command_start)shelp%(command_end)s and press enter.",
                        **self._get_style_dict()
                    )
                elif odoobot_state == 'onboarding_ping':
                    self.env.user.odoobot_failed = True
                    return self.env._(
                        "Sorry, I am not listening. To get someone's attention, %(bold_start)sping "
                        "him%(bold_end)s. Write %(command_start)s@OdooBot%(command_end)s and select"
                        " me.",
                        **self._get_style_dict()
                    )
                return random.choice(
                    [
                        self.env._(
                            "I'm not smart enough to answer your question.%(new_line)sTo follow my "
                            "guide, ask: %(command_start)sstart the tour%(command_end)s.",
                            **self._get_style_dict()
                        ),
                        self.env._("Hmmm..."),
                        self.env._("I'm afraid I don't understand. Sorry!"),
                        self.env._(
                            "Sorry I'm sleepy. Or not! Maybe I'm just trying to hide my unawareness"
                            " of human language...%(new_line)sI can show you features if you write:"
                            " %(command_start)sstart the tour%(command_end)s.",
                            **self._get_style_dict()
                        ),
                    ]
                )
        return False
async def _parse_speak(self, memories):
        latest_msg = memories[-1]
        latest_msg_content = latest_msg.content

        match = re.search(r"Player[0-9]+", latest_msg_content[-10:])  # FIXME: hard code truncation
        target = match.group(0) if match else ""

        # default return
        msg_content = "Understood"
        restricted_to = set()

        msg_cause_by = latest_msg.cause_by
        if msg_cause_by == any_to_str(Hunt):
            self.rc.env.step(
                EnvAction(
                    action_type=EnvActionType.WOLF_KILL, player_name=latest_msg.sent_from, target_player_name=target
                )
            )
        elif msg_cause_by == any_to_str(Protect):
            self.rc.env.step(
                EnvAction(
                    action_type=EnvActionType.GUARD_PROTECT, player_name=latest_msg.sent_from, target_player_name=target
                )
            )
        elif msg_cause_by == any_to_str(Verify):
            if target in self.werewolf_players:
                msg_content = f"{target} is a werewolf"
            else:
                msg_content = f"{target} is a good guy"
            restricted_to = {RoleType.MODERATOR.value, RoleType.SEER.value}
        elif msg_cause_by == any_to_str(Save):
            if RoleActionRes.PASS.value in latest_msg_content.lower():
                # the role ignore to response, answer `pass`
                pass
            elif not self.witch_antidote_left:
                msg_content = "You have no antidote left and thus can not save the player"
                restricted_to = {RoleType.MODERATOR.value, RoleType.WITCH.value}
            else:
                self.rc.env.step(
                    EnvAction(
                        action_type=EnvActionType.WITCH_SAVE,
                        player_name=latest_msg.sent_from,
                        target_player_name=target,
                    )
                )
        elif msg_cause_by == any_to_str(Poison):
            if RoleActionRes.PASS.value in latest_msg_content.lower():
                pass
            elif not self.witch_poison_left:
                msg_content = "You have no poison left and thus can not poison the player"
                restricted_to = {RoleType.MODERATOR.value, RoleType.WITCH.value}
            else:
                self.rc.env.step(
                    EnvAction(
                        action_type=EnvActionType.WITCH_POISON,
                        player_name=latest_msg.sent_from,
                        target_player_name=target,
                    )
                )

        return msg_content, restricted_to
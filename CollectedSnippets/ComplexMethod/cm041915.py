def publish_message(self, message: Message, user_defined_recipient: str = "", publicer: str = "") -> bool:
        """let the team leader take over message publishing"""
        message = self.attach_images(message)  # for multi-modal message

        tl = self.get_role(TEAMLEADER_NAME)  # TeamLeader's name is Mike

        if user_defined_recipient:
            # human user's direct chat message to a certain role
            for role_name in message.send_to:
                if self.get_role(role_name).is_idle:
                    # User starts a new direct chat with a certain role, expecting a direct chat response from the role; Other roles including TL should not be involved.
                    # If the role is not idle, it means the user helps the role with its current work, in this case, we handle the role's response message as usual.
                    self.direct_chat_roles.add(role_name)

            self._publish_message(message)
            # # bypass team leader, team leader only needs to know but not to react (commented out because TL doesn't understand the message well in actual experiments)
            # tl.rc.memory.add(self.move_message_info_to_content(message))

        elif message.sent_from in self.direct_chat_roles:
            # if chat is not public, direct chat response from a certain role to human user, team leader and other roles in the env should not be involved, no need to publish
            self.direct_chat_roles.remove(message.sent_from)
            if self.is_public_chat:
                self._publish_message(message)

        elif publicer == tl.profile:
            if message.send_to == {"no one"}:
                # skip the dummy message from team leader
                return True
            # message processed by team leader can be published now
            self._publish_message(message)

        else:
            # every regular message goes through team leader
            message.send_to.add(tl.name)
            self._publish_message(message)

        self.history.add(message)

        return True
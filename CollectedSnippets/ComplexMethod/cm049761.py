def session_call_notify(self, peer_notifications):
        """Sends content to other session of the same channel, only works if the user is the user of that session.
        This is used to send peer to peer information between sessions.

        :param peer_notifications: list of tuple with the following elements:
            - int sender_session_id: id of the session from which the content is sent
            - list target_session_ids: list of the ids of the sessions that should receive the content
            - string content: the content to send to the other sessions
        """
        guest = request.env["mail.guest"]._get_guest_from_context()
        notifications_by_session = defaultdict(list)
        for sender_session_id, target_session_ids, content in peer_notifications:
            # sudo: discuss.channel.rtc.session - only keeping sessions matching the current user
            session_sudo = request.env["discuss.channel.rtc.session"].sudo().browse(int(sender_session_id)).exists()
            if (
                not session_sudo
                or (session_sudo.guest_id and session_sudo.guest_id != guest)
                or (session_sudo.partner_id and session_sudo.partner_id != request.env.user.partner_id)
            ):
                continue
            notifications_by_session[session_sudo].append(([int(sid) for sid in target_session_ids], content))
        for session_sudo, notifications in notifications_by_session.items():
            session_sudo._notify_peers(notifications)
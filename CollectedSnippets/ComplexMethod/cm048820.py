def _dispatch_bus_notifications(self):
        """
        Dispatch notifications related to the registered channels. If
        the session is expired, close the connection with the
        `SESSION_EXPIRED` close code. If no cursor can be acquired,
        close the connection with the `TRY_LATER` close code.
        """
        session = root.session_store.get(self._session.sid)
        if not session:
            raise SessionExpiredException()
        if 'next_sid' in session:
            self._session = root.session_store.get(session['next_sid'])
            return self._dispatch_bus_notifications()
         # Mark the notification request as processed.
        self._waiting_for_dispatch = False
        with acquire_cursor(session.db) as cr:
            env = self.new_env(cr, session)
            if session.uid is not None and not check_session(session, env):
                raise SessionExpiredException()
            notifications = env["bus.bus"]._poll(
                self._channels, self._last_notif_sent_id, [n[0] for n in self._notif_history]
            )
        if not notifications:
            return
        for notif in notifications:
            bisect.insort(self._notif_history, (notif["id"], time.time()), key=lambda x: x[0])
        # Discard all the smallest notification ids that have expired and
        # increment the last id accordingly. History can only be trimmed of ids
        # that are below the new last id otherwise some notifications might be
        # dispatched again.
        # For example, if the theshold is 10s, and the state is:
        # last id 2, history [(3, 8s), (6, 10s), (7, 7s)]
        # If 6 is removed because it is above the threshold, the next query will
        # be (id > 2 AND id NOT IN (3, 7)) which will fetch 6 again.
        # 6 can only be removed after 3 reaches the threshold and is removed as
        # well, and if 4 appears in the meantime, 3 can be removed but 6 will
        # have to wait for 4 to reach the threshold as well.
        last_index = -1
        for i, notif in enumerate(self._notif_history):
            if time.time() - notif[1] > self.MAX_NOTIFICATION_HISTORY_SEC:
                last_index = i
            else:
                break
        if last_index != -1:
            self._last_notif_sent_id = self._notif_history[last_index][0]
            self._notif_history = self._notif_history[last_index + 1 :]
        self._send(notifications)
def _set_session_inactivity(self, session, inactivity_period=0, force=False):
        """
        Set or clear the session's inactivity timeout flag.

        This method is used to track user inactivity and determine when a session
        should trigger re-authentication. It is called when presence data is received
        through the websocket, either:

        - because the web client, in Javascript, sent an event that the user is inactive
        - because the websocket connection was closed (e.g., the user closed the browser,
          the last tab to Odoo was closed, internet disconnection, ...)

        :param Session session: The user's HTTP session object.
        :param float inactivity_period: Duration of user inactivity in milliseconds.
        :param bool force: If True, forcibly mark the session as inactive regardless of duration.
            This is typically used when the WebSocket connection is closed (e.g., the user closes
            their last browser tab), signaling that the user has gone away. The inactivity timeout
            still applies in this case. If the user becomes active again (e.g., reopens the tab)
            before the threshold is reached, the session will be considered active again,
            and re-authentication will not be required.

        :return: None
        """
        # inactivity_period sent by the js is in milliseconds
        inactivity_period = inactivity_period / 1000
        timeout = self.env.user._get_lock_timeout_inactivity()
        inactive = timeout and (force or inactivity_period >= timeout)
        if inactive:
            next_check = time.time() + timeout - inactivity_period
            if not session.get("identity-check-next") or next_check < session["identity-check-next"]:
                session["identity-check-next"] = next_check
                # Save manually, websocket requests do not save the session automatically
                root.session_store.save(session)
        elif not inactive and (timestamp := session.get("identity-check-next")) and timestamp > time.time():
            session.pop("identity-check-next")
            # Save manually, websocket requests do not save the session automatically
            root.session_store.save(session)
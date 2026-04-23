def _must_check_identity(cls):
        """
        Determine whether the current user session requires identity confirmation.

        This method checks two timeout conditions:
        - `lock_timeout`: maximum allowed session duration before re-authentication is required,
        regardless of user activity.
        - `lock_timeout_inactivity`: period of inactivity after which re-authentication is required.

        It compares the current time to session timestamps and evaluates whether the thresholds have been exceeded:
        - `lock_timeout` compares with the session timestamp `create_time`
        - `lock_timeout_inactivity` compares with the session timestamp `identity-check-next`

        :return: A dictionary describing the re-authentication requirement, or None if no check is needed.

            Possible keys:
            - "logout": True if a full logout is required
            - "check_identity": True if an identity check is required
            - "mfa": True if multi-factor authentication is required
            - "1fa": previously used auth method, to avoid reuse as second factor

        :rtype: dict or None
        """
        session = request.session
        env = request.env(user=request.session.uid)
        timeouts = env.user._get_lock_timeouts()
        for timeout_type, reauth_type, session_key, session_key_default, first_timeout in [
            ("lock_timeout", "logout", "create_time", 0, 0),
            (
                "lock_timeout_inactivity",
                "check_identity",
                "identity-check-next",
                None,
                timeouts["lock_timeout_inactivity"][0][0] if timeouts.get("lock_timeout_inactivity") else 0,
            ),
        ]:
            for timeout, mfa in reversed(timeouts[timeout_type]):
                threshold = time.time() - timeout
                timestamp = session.get(session_key, session_key_default)
                # Only the lowest inactivity timeout will set `identity-check-next` in the session
                # Hence, an inactivity timeout with a greater timeout must reduce its timeout with the first timeout
                # to get if its timeout is reached according to when `identity-check-next` was set at the lowest timeout
                # It doesn't apply for `create_time`, which is set as soon as the session is created
                if timestamp is not None and timestamp - first_timeout <= threshold:
                    res = {reauth_type: True, "mfa": mfa}
                    if mfa:
                        first_fa = session.get("identity-check-1fa")
                        if first_fa:
                            timestamp_1fa, auth_method_1fa = first_fa
                            if timestamp_1fa > threshold:
                                res["1fa"] = auth_method_1fa
                    return res
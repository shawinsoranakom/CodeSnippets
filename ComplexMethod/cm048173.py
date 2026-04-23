def _check_identity(cls, credential):
        """
        Verify the user's identity using the given credentials.

        Handles both single and multi-factor authentication flows depending on the
        current session state and configured timeout rules.

        :param dict credential: A dictionary containing authentication data. Must include
            a "type" key (e.g., "password", "totp", "webauthn"). If empty, the method
            returns the list of available authentication methods.

        :return: A dictionary indicating the outcome of the identity check:

            - {"auth_methods": [...]} if no credential is provided,
            - {"mfa": True, "auth_methods": [...]} if a second factor is required,
            - None if re-authentication is complete.

        :rtype: dict or None
        """
        check_identity = cls._must_check_identity() or {}
        first_fa = check_identity.get("1fa")
        user = request.env.user
        auth_methods = user._get_auth_methods()
        if not credential:
            if first_fa and first_fa in auth_methods:
                auth_methods.remove(first_fa)
            return {"user_id": user.id, "login": user.login, "auth_methods": auth_methods}

        if credential.get("type") in ("totp", "totp_mail"):
            credential["token"] = int(re.sub(r"\s", "", credential["token"]))

        auth = user._check_credentials(credential, {"interactive": True})

        if first_fa and first_fa != auth["auth_method"]:
            request.session.pop("identity-check-1fa")
        elif auth["mfa"] != "skip" and len(auth_methods) > 1 and check_identity.get("mfa"):
            request.session["identity-check-1fa"] = (time.time(), credential["type"])
            auth_methods.remove(credential["type"])
            return {"mfa": True, "auth_methods": auth_methods}

        request.session.pop("identity-check-next", None)
        request.session["identity-check-last"] = time.time()
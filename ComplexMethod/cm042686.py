def policy(
        self,
        response: Response | str | None = None,
        request: Request | None = None,
        **kwargs: Unpack[_PolicyKwargs],
    ) -> ReferrerPolicy:
        """Return the referrer policy to use for *request* based on *request*
        meta, *response* and settings.

        - if a valid policy is set in Request meta, it is used.
        - if the policy is set in meta but is wrong (e.g. a typo error), the
          policy from settings is used
        - if the policy is not set in Request meta, but there is a
          Referrer-Policy header in the parent response, it is used if valid
        - otherwise, the policy from settings is used.
        """
        if "resp_or_url" in kwargs:
            if response is not None:
                raise TypeError("Cannot pass both 'response' and 'resp_or_url'")
            response = kwargs.pop("resp_or_url")
            warn(
                "Passing 'resp_or_url' is deprecated, use 'response' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if response is None:
            raise TypeError("Missing required argument: 'response'")
        if request is None:
            raise TypeError("Missing required argument: 'request'")
        if isinstance(response, str):
            warn(
                "Passing a response URL to RefererMiddleware.policy() instead "
                "of a Response object is deprecated.",
                DeprecationWarning,
                stacklevel=2,
            )
        allow_import_path = True
        policy_name = request.meta.get("referrer_policy")
        if policy_name is None and isinstance(response, Response):
            policy_header = response.headers.get("Referrer-Policy")
            if policy_header is not None:
                policy_name = to_unicode(policy_header.decode("latin1"))
                allow_import_path = False
        if policy_name is None:
            return self.default_policy()
        cls = self._load_policy_class(
            policy_name, warning_only=True, allow_import_path=allow_import_path
        )
        return cls() if cls else self.default_policy()
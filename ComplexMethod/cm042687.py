def _load_policy_class(
        self,
        policy: str,
        warning_only: bool = False,
        *,
        allow_import_path: bool = False,
    ) -> type[ReferrerPolicy] | None:
        """Load the :class:`ReferrerPolicy` class to use for *policy*.

        *policy* may be any of the following:

        -   A standard policy name, e.g. ``"no-referrer"``,
            ``"origin-when-cross-origin"``, etc.

        -   The special ``"scrapy-default"`` policy.

        -   The import path of a :class:`ReferrerPolicy` subclass, e.g.
            ``"scrapy.spidermiddlewares.referer.NoReferrerPolicy"`` or
            ``"myproject.policies.CustomReferrerPolicy"``.

        If *warning_only* is ``False`` (default) and *policy* cannot be turned
        into a :class:`ReferrerPolicy` subclass, a :exc:`RuntimeError` is
        raised. If *warning_only* is ``True``, a warning is logged and ``None``
        is returned instead.

        If *allow_import_path* is ``False`` (default), import paths are not
        allowed, resulting in :exc:`RuntimeError` or ``None``. If ``True``,
        they are allowed. Use ``True`` only if you trust the source of the
        *policy* value.
        """
        if allow_import_path:
            try:
                return cast("type[ReferrerPolicy]", load_object(policy))
            except ValueError:
                pass
        policy_names = [
            policy_name.strip() for policy_name in policy.lower().split(",")
        ]
        # https://www.w3.org/TR/referrer-policy/#parse-referrer-policy-from-header
        for policy_name in policy_names[::-1]:
            if policy_name in self.policies:
                return self.policies[policy_name]
        msg = f"Could not load referrer policy {policy!r}"
        if not allow_import_path and _looks_like_import_path(policy):
            msg += " (import paths from the response Referrer-Policy header are not allowed)"
        if not warning_only:
            raise RuntimeError(msg)
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        return None
def _get_lock_timeouts(self):
        """
        Compute the session and inactivity timeout settings for the user.

        This method returns the shortest configured timeouts (in seconds) across all groups
        implied by the user's group membership. For each type of timeout, it distinguishes
        between those that require MFA and those that do not.

        :return: A dictionary with timeout types as keys and a list of tuples as values.
            Each tuple is of the form (timeout_in_seconds, requires_mfa), ordered from shortest to longest.

            Example::

                {
                    'lock_timeout': [(43200, False), (86400, True)],
                    'lock_timeout_inactivity': [(900, False)]
                }

        :rtype: dict
        """
        result = {}

        for key, mfa_key in [
            ("lock_timeout", "lock_timeout_mfa"),
            ("lock_timeout_inactivity", "lock_timeout_inactivity_mfa"),
        ]:
            # `with_context({})` because
            # - Same reasons than https://github.com/odoo/odoo/commit/7a0255665714f2c0129d04d4a3f14a3137c159f1
            # - As this method is decorated with `@ormcache('self._ids')`, it cannot depend on the context
            values = [(g[key], g[mfa_key]) for g in self.with_context({}).all_implied_ids if g[key]]
            min_non_mfa = min((timeout for timeout, mfa in values if not mfa), default=None)
            min_mfa = min((timeout for timeout, mfa in values if mfa), default=None)

            result[key] = []

            if min_mfa:
                result[key].append((min_mfa * 60, True))
            if min_non_mfa and (not min_mfa or min_non_mfa < min_mfa):
                result[key].append((min_non_mfa * 60, False))

            # Sort from lowest timeout to highest
            result[key].sort()

        return result
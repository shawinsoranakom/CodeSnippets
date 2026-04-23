def check_referrer_policy(app_configs, **kwargs):
    if _security_middleware():
        if settings.SECURE_REFERRER_POLICY is None:
            return [W022]
        # Support a comma-separated string or iterable of values to allow
        # fallback.
        if isinstance(settings.SECURE_REFERRER_POLICY, str):
            values = {v.strip() for v in settings.SECURE_REFERRER_POLICY.split(",")}
        else:
            values = set(settings.SECURE_REFERRER_POLICY)
        if not values <= REFERRER_POLICY_VALUES:
            return [E023]
    return []
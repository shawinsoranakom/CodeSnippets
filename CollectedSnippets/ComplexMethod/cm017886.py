def build_policy(config, nonce=None):
    policy = []

    for directive, values in config.items():
        if values in (None, False):
            continue

        if values is True:
            rendered_value = ""
        else:
            if isinstance(values, set):
                # Sort values for consistency, preventing cache invalidation
                # between requests and ensuring reliable browser caching.
                values = sorted(values)
            elif not isinstance(values, list | tuple):
                values = [values]

            # Replace the nonce sentinel with the actual nonce values, if the
            # sentinel is found and a nonce is provided. Otherwise, remove it.
            if (has_sentinel := CSP.NONCE in values) and nonce:
                values = [f"'nonce-{nonce}'" if v == CSP.NONCE else v for v in values]
            elif has_sentinel:
                values = [v for v in values if v != CSP.NONCE]

            if not values:
                continue

            rendered_value = " ".join(values)

        policy.append(f"{directive} {rendered_value}".rstrip())

    return "; ".join(policy)
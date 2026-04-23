def _availability(is_private=None, needs_premium=None, needs_subscription=None, needs_auth=None, is_unlisted=None):
        all_known = all(
            x is not None for x in
            (is_private, needs_premium, needs_subscription, needs_auth, is_unlisted))
        return (
            'private' if is_private
            else 'premium_only' if needs_premium
            else 'subscriber_only' if needs_subscription
            else 'needs_auth' if needs_auth
            else 'unlisted' if is_unlisted
            else 'public' if all_known
            else None)
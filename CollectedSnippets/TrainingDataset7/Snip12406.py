def has_listeners(self, sender=None):
        sync_receivers, async_receivers = self._live_receivers(sender)
        return bool(sync_receivers) or bool(async_receivers)
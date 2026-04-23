def async_register_callback(
        self,
        callback: BluetoothCallback,
        matcher: BluetoothCallbackMatcher | None,
    ) -> Callable[[], None]:
        """Register a callback."""
        callback_matcher = BluetoothCallbackMatcherWithCallback(callback=callback)
        if not matcher:
            callback_matcher[CONNECTABLE] = True
        else:
            # We could write out every item in the typed dict here
            # but that would be a bit inefficient and verbose.
            callback_matcher.update(matcher)
            callback_matcher[CONNECTABLE] = matcher.get(CONNECTABLE, True)

        connectable = callback_matcher[CONNECTABLE]
        self._callback_index.add_callback_matcher(callback_matcher)

        def _async_remove_callback() -> None:
            self._callback_index.remove_callback_matcher(callback_matcher)

        # If we have history for the subscriber, we can trigger the callback
        # immediately with the last packet so the subscriber can see the
        # device.
        history = self._connectable_history if connectable else self._all_history
        service_infos: Iterable[BluetoothServiceInfoBleak] = []
        if address := callback_matcher.get(ADDRESS):
            if service_info := history.get(address):
                service_infos = [service_info]
        else:
            service_infos = history.values()

        for service_info in service_infos:
            if ble_device_matches(callback_matcher, service_info):
                try:
                    callback(service_info, BluetoothChange.ADVERTISEMENT)
                except Exception:
                    _LOGGER.exception("Error in bluetooth callback")

        return _async_remove_callback
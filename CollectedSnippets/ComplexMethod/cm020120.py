async def assert_telegram(
        self,
        group_address: str,
        payload: int | tuple[int, ...] | None,
        apci_type: type[APCI],
        ignore_order: bool = False,
    ) -> None:
        """Assert outgoing telegram. Optionally in timely order."""
        await self.xknx.telegrams.join()
        if not self._outgoing_telegrams:
            raise AssertionError(
                f"No Telegram found. Expected: {apci_type.__name__} -"
                f" {group_address} - {payload}"
            )
        _expected_ga = GroupAddress(group_address)

        if ignore_order:
            for telegram in self._outgoing_telegrams:
                if (
                    telegram.destination_address == _expected_ga
                    and isinstance(telegram.payload, apci_type)
                    and (payload is None or telegram.payload.value.value == payload)
                ):
                    self._outgoing_telegrams.remove(telegram)
                    return
            raise AssertionError(
                f"Telegram not found. Expected: {apci_type.__name__} -"
                f" {group_address} - {payload}"
                f"\nUnasserted telegrams:\n{self._list_remaining_telegrams()}"
            )

        telegram = self._outgoing_telegrams.pop(0)
        assert isinstance(telegram.payload, apci_type), (
            f"APCI type mismatch in {telegram} - Expected: {apci_type.__name__}"
        )
        assert telegram.destination_address == _expected_ga, (
            f"Group address mismatch in {telegram} - Expected: {group_address}"
        )
        if payload is not None:
            assert (
                telegram.payload.value.value == payload  # type: ignore[attr-defined]
            ), f"Payload mismatch in {telegram} - Expected: {payload}"
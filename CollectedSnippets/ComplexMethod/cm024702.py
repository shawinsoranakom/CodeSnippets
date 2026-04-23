async def mock_get_characteristics(
        chars: set[tuple[int, int]], **kwargs: Any
    ) -> dict[tuple[int, int], dict[str, Any]]:
        """Return fresh temperature value when polled."""
        polled_chars.extend(chars)
        # Return fresh values for all characteristics
        result: dict[tuple[int, int], dict[str, Any]] = {}
        for aid, iid in chars:
            # Find the characteristic and return appropriate value
            for accessory in accessories:
                if accessory.aid != aid:
                    continue
                for service in accessory.services:
                    for char in service.characteristics:
                        if char.iid != iid:
                            continue
                        # Return fresh temperature instead of stale fixture value
                        if char.type == CharacteristicsTypes.TEMPERATURE_CURRENT:
                            result[(aid, iid)] = {"value": 22.5}  # Fresh value
                        else:
                            result[(aid, iid)] = {"value": char.value}
                        break
        return result
def _device_count_amdsmi() -> int:
    visible_devices = _parse_visible_devices()
    if not visible_devices:
        return 0
    try:
        if type(visible_devices[0]) is str:
            uuids = _raw_device_uuid_amdsmi()
            if uuids is None:
                return -1
            # Create string version of visible devices to avoid mypy warnings
            visible_device_str = cast(list[str], visible_devices)
            visible_devices = _transform_uuid_to_ordinals(visible_device_str, uuids)
        else:
            raw_cnt = _raw_device_count_amdsmi()
            if raw_cnt <= 0:
                return raw_cnt
            # Trim the list up to a maximum available device
            # pyrefly: ignore [bad-argument-type]
            for idx, val in enumerate(visible_devices):
                # pyrefly: ignore [redundant-cast]
                if cast(int, val) >= raw_cnt:
                    return idx
    except OSError:
        return -1
    except AttributeError:
        return -1
    return len(visible_devices)
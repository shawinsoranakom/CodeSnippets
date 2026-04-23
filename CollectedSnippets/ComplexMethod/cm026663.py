async def update_slides(now=None):
        """Update slide information."""
        result = await hass.data[DOMAIN][API].slides_overview()

        if result is None:
            _LOGGER.error("Slide API does not work or returned an error")
            return

        if result:
            _LOGGER.debug("Slide API returned %d slide(s)", len(result))
        else:
            _LOGGER.warning("Slide API returned 0 slides")

        for slide in result:
            if "device_id" not in slide:
                _LOGGER.error(
                    "Found invalid Slide entry, device_id is missing. Entry=%s", slide
                )
                continue

            uid = slide["device_id"].replace("slide_", "")
            slidenew = hass.data[DOMAIN][SLIDES].setdefault(uid, {})
            slidenew["mac"] = uid
            slidenew["id"] = slide["id"]
            slidenew["name"] = slide["device_name"]
            slidenew["state"] = None
            oldpos = slidenew.get("pos")
            slidenew["pos"] = None
            slidenew["online"] = False
            slidenew["invert"] = config[DOMAIN][CONF_INVERT_POSITION]

            if "device_info" not in slide:
                _LOGGER.error(
                    "Slide %s (%s) has no device_info Entry=%s",
                    slide["id"],
                    slidenew["mac"],
                    slide,
                )
                continue

            # Check if we have pos (OK) or code (NOK)
            if "pos" in slide["device_info"]:
                slidenew["online"] = True
                slidenew["pos"] = slide["device_info"]["pos"]
                slidenew["pos"] = max(0, min(1, slidenew["pos"]))

                if oldpos is None or oldpos == slidenew["pos"]:
                    slidenew["state"] = (
                        STATE_CLOSED
                        if slidenew["pos"] > (1 - DEFAULT_OFFSET)
                        else STATE_OPEN
                    )
                elif oldpos < slidenew["pos"]:
                    slidenew["state"] = (
                        STATE_CLOSED
                        if slidenew["pos"] >= (1 - DEFAULT_OFFSET)
                        else STATE_CLOSING
                    )
                else:
                    slidenew["state"] = (
                        STATE_OPEN
                        if slidenew["pos"] <= DEFAULT_OFFSET
                        else STATE_OPENING
                    )
            elif "code" in slide["device_info"]:
                _LOGGER.warning(
                    "Slide %s (%s) is offline with code=%s",
                    slide["id"],
                    slidenew["mac"],
                    slide["device_info"]["code"],
                )
            else:
                _LOGGER.error(
                    "Slide %s (%s) has invalid device_info %s",
                    slide["id"],
                    slidenew["mac"],
                    slide["device_info"],
                )

            _LOGGER.debug("Updated entry=%s", slidenew)
def async_call_trigger_action(
        telegram: Telegram, telegram_dict: TelegramDict
    ) -> None:
        """Filter Telegram and call trigger action."""
        payload_apci = type(telegram.payload)
        if payload_apci is GroupValueWrite:
            if config[CONF_KNX_GROUP_VALUE_WRITE] is False:
                return
        elif payload_apci is GroupValueResponse:
            if config[CONF_KNX_GROUP_VALUE_RESPONSE] is False:
                return
        elif payload_apci is GroupValueRead:
            if config[CONF_KNX_GROUP_VALUE_READ] is False:
                return

        if telegram.direction is TelegramDirection.INCOMING:
            if config[CONF_KNX_INCOMING] is False:
                return
        elif config[CONF_KNX_OUTGOING] is False:
            return

        if dst_addresses and telegram.destination_address not in dst_addresses:
            return

        if (
            trigger_transcoder is not None
            and payload_apci in (GroupValueWrite, GroupValueResponse)
            and trigger_transcoder.value_type != telegram_dict["dpt_name"]
        ):
            decoded_payload = decode_telegram_payload(
                payload=telegram.payload.value,  # type: ignore[union-attr]  # checked via payload_apci
                transcoder=trigger_transcoder,
            )
            # overwrite decoded payload values in telegram_dict
            telegram_trigger_data = {**trigger_data, **telegram_dict, **decoded_payload}
        else:
            telegram_trigger_data = {**trigger_data, **telegram_dict}

        hass.async_run_hass_job(job, {"trigger": telegram_trigger_data})
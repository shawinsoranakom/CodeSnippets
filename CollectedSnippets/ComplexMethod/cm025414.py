async def _set_dataset(self, api: python_otbr_api.OTBR, otbr_url: str) -> None:
        """Connect to the OTBR and create or apply a dataset if it doesn't have one."""
        if await api.get_active_dataset_tlvs() is None:
            allowed_channel = await get_allowed_channel(self.hass, otbr_url)

            thread_dataset_channel = None
            thread_dataset_tlv = await async_get_preferred_dataset(self.hass)
            if thread_dataset_tlv:
                dataset = tlv_parser.parse_tlv(thread_dataset_tlv)
                if channel := dataset.get(MeshcopTLVType.CHANNEL):
                    thread_dataset_channel = cast(tlv_parser.Channel, channel).channel

            if thread_dataset_tlv is not None and (
                not allowed_channel or allowed_channel == thread_dataset_channel
            ):
                await api.set_active_dataset_tlvs(bytes.fromhex(thread_dataset_tlv))
            else:
                _LOGGER.debug(
                    "not importing TLV with channel %s for %s",
                    thread_dataset_channel,
                    otbr_url,
                )
                pan_id = generate_random_pan_id()
                await api.create_active_dataset(
                    python_otbr_api.ActiveDataSet(
                        channel=allowed_channel or DEFAULT_CHANNEL,
                        network_name=compose_default_network_name(pan_id),
                        pan_id=pan_id,
                    )
                )
            await api.set_enabled(True)
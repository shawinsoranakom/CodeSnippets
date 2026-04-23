def _warn_on_default_network_settings(
    hass: HomeAssistant, otbrdata: OTBRData, dataset_tlvs: bytes
) -> None:
    """Warn user if insecure default network settings are used."""
    dataset = tlv_parser.parse_tlv(dataset_tlvs.hex())
    insecure = False

    if (
        network_key := dataset.get(MeshcopTLVType.NETWORKKEY)
    ) is not None and network_key.data in INSECURE_NETWORK_KEYS:
        insecure = True
    if (
        not insecure
        and MeshcopTLVType.EXTPANID in dataset
        and MeshcopTLVType.NETWORKNAME in dataset
        and MeshcopTLVType.PSKC in dataset
    ):
        ext_pan_id = dataset[MeshcopTLVType.EXTPANID]
        network_name = cast(tlv_parser.NetworkName, dataset[MeshcopTLVType.NETWORKNAME])
        pskc = dataset[MeshcopTLVType.PSKC].data
        for passphrase in INSECURE_PASSPHRASES:
            if pskc == compute_pskc(ext_pan_id.data, network_name.name, passphrase):
                insecure = True
                break

    if insecure:
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"insecure_thread_network_{otbrdata.entry_id}",
            is_fixable=False,
            is_persistent=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="insecure_thread_network",
        )
    else:
        ir.async_delete_issue(
            hass,
            DOMAIN,
            f"insecure_thread_network_{otbrdata.entry_id}",
        )
def _data_secure_group_key_issue_handler(
    knx_module: KNXModule, telegram: Telegram, telegram_dict: TelegramDict
) -> None:
    """Handle DataSecure group key issue telegrams."""
    if telegram.destination_address not in knx_module.group_address_entities:
        # Only report issues for configured group addresses
        return

    issue_registry = ir.async_get(knx_module.hass)
    new_ga = str(telegram.destination_address)
    new_ia = str(telegram.source_address)
    new_data = {new_ga: new_ia}

    if existing_issue := issue_registry.async_get_issue(
        DOMAIN, REPAIR_ISSUE_DATA_SECURE_GROUP_KEY
    ):
        assert isinstance(existing_issue.data, dict)
        existing_data: dict[str, str] = existing_issue.data  # type: ignore[assignment]
        if new_ga in existing_data:
            current_ias = existing_data[new_ga].split(", ")
            if new_ia in current_ias:
                return
            current_ias = sorted([*current_ias, new_ia], key=IndividualAddress)
            new_data[new_ga] = ", ".join(current_ias)
        new_data_unsorted = existing_data | new_data
        new_data = {
            key: new_data_unsorted[key]
            for key in sorted(new_data_unsorted, key=GroupAddress)
        }

    issue_registry.async_get_or_create(
        DOMAIN,
        REPAIR_ISSUE_DATA_SECURE_GROUP_KEY,
        data=new_data,  # type: ignore[arg-type]
        is_fixable=True,
        is_persistent=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key=REPAIR_ISSUE_DATA_SECURE_GROUP_KEY,
        translation_placeholders={
            "addresses": "\n".join(
                f"`{ga}` from {ias}" for ga, ias in new_data.items()
            ),
            "interface": str(knx_module.xknx.current_address),
        },
    )
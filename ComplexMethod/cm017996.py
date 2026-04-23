async def test_as_dict(snapshot: SnapshotAssertion) -> None:
    """Test ConfigEntry.as_dict."""

    # Ensure as_dict is not overridden
    assert MockConfigEntry.as_dict is config_entries.ConfigEntry.as_dict

    excluded_from_dict = {
        "supports_unload",
        "supports_remove_device",
        "state",
        "_setup_lock",
        "update_listeners",
        "reason",
        "error_reason_translation_key",
        "error_reason_translation_placeholders",
        "_async_cancel_retry_setup",
        "_on_unload",
        "setup_lock",
        "_reauth_lock",
        "_tasks",
        "_background_tasks",
        "_integration_for_domain",
        "_tries",
        "_setup_again_job",
        "_supports_options",
        "supports_reconfigure",
    }

    entry = MockConfigEntry(entry_id="mock-entry")

    # Make sure the expected keys are present
    dict_repr = entry.as_dict()
    for key in config_entries.ConfigEntry.__dict__:
        func = getattr(config_entries.ConfigEntry, key)
        if (
            key.startswith("__")
            or callable(func)
            or type(func).__name__ in ("cached_property", "property")
        ):
            continue
        assert key in dict_repr or key in excluded_from_dict
        assert not (key in dict_repr and key in excluded_from_dict)

    # Make sure the dict representation is as expected
    assert dict_repr == snapshot
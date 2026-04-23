async def test_get_subentries_of_type(hass: HomeAssistant) -> None:
    """Test getting subentries by type."""
    entry = MockConfigEntry(
        domain="test",
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={},
                subentry_type="test",
                title="Mock title",
                unique_id="unique",
            ),
            config_entries.ConfigSubentryData(
                data={},
                subentry_type="test",
                title="Mock title 2",
                unique_id="very_very_unique",
            ),
            config_entries.ConfigSubentryData(
                data={},
                subentry_type="test_test",
                title="Mock title 3",
                unique_id="very_unique",
            ),
        ],
    )

    test_subentries = entry.get_subentries_of_type("test")
    assert len(test_subentries) == 2
    assert [subentry.unique_id for subentry in test_subentries] == [
        "unique",
        "very_very_unique",
    ]
    assert all(subentry.subentry_type == "test" for subentry in test_subentries)
    assert len({subentry.subentry_id for subentry in test_subentries}) == len(
        test_subentries
    )

    test_test_subentries = entry.get_subentries_of_type("test_test")
    assert len(test_test_subentries) == 1
    assert test_test_subentries[0].unique_id == "very_unique"
    assert test_test_subentries[0].subentry_type == "test_test"

    assert entry.get_subentries_of_type("unknown") == []
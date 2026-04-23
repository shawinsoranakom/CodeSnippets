async def test_unique_id_collision_issues(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    caplog: pytest.LogCaptureFixture,
    issue_registry: ir.IssueRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test issue registry issues are created and remove on unique id collision."""
    assert len(issue_registry.issues) == 0

    mock_setup_entry = AsyncMock(return_value=True)
    for i in range(3):
        mock_integration(
            hass, MockModule(f"test{i + 1}", async_setup_entry=mock_setup_entry)
        )
        mock_platform(hass, f"test{i + 1}.config_flow", None)

    test2_group_1: list[MockConfigEntry] = []
    test2_group_2: list[MockConfigEntry] = []
    test3: list[MockConfigEntry] = []
    for _ in range(3):
        await manager.async_add(MockConfigEntry(domain="test1", unique_id=None))
        test2_group_1.append(MockConfigEntry(domain="test2", unique_id="group_1"))
        test2_group_2.append(MockConfigEntry(domain="test2", unique_id="group_2"))
        await manager.async_add(test2_group_1[-1])
        await manager.async_add(test2_group_2[-1])
    for _ in range(6):
        test3.append(MockConfigEntry(domain="test3", unique_id="not_unique"))
        await manager.async_add(test3[-1])
    # Add an ignored config entry
    await manager.async_add(
        MockConfigEntry(
            domain="test2", unique_id="group_1", source=config_entries.SOURCE_IGNORE
        )
    )

    # Check we get one issue for domain test2 and one issue for domain test3
    assert len(issue_registry.issues) == 2
    issue_id = "config_entry_unique_id_collision_test2_group_1"
    assert issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id) == snapshot
    issue_id = "config_entry_unique_id_collision_test3_not_unique"
    assert issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id) == snapshot

    # Remove one config entry for domain test3, the translations should be updated
    await manager.async_remove(test3[0].entry_id)
    assert set(issue_registry.issues) == {
        (HOMEASSISTANT_DOMAIN, "config_entry_unique_id_collision_test2_group_1"),
        (HOMEASSISTANT_DOMAIN, "config_entry_unique_id_collision_test3_not_unique"),
    }
    assert issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id) == snapshot

    # Remove all but two config entries for domain test 3
    for i in range(3):
        await manager.async_remove(test3[1 + i].entry_id)
        assert set(issue_registry.issues) == {
            (HOMEASSISTANT_DOMAIN, "config_entry_unique_id_collision_test2_group_1"),
            (HOMEASSISTANT_DOMAIN, "config_entry_unique_id_collision_test3_not_unique"),
        }

    # Remove the last test3 duplicate, the issue is cleared
    await manager.async_remove(test3[-1].entry_id)
    assert set(issue_registry.issues) == {
        (HOMEASSISTANT_DOMAIN, "config_entry_unique_id_collision_test2_group_1"),
    }

    await manager.async_remove(test2_group_1[0].entry_id)
    assert set(issue_registry.issues) == {
        (HOMEASSISTANT_DOMAIN, "config_entry_unique_id_collision_test2_group_1"),
    }

    # Remove the last test2 group1 duplicate, a new issue is created
    await manager.async_remove(test2_group_1[1].entry_id)
    assert set(issue_registry.issues) == {
        (HOMEASSISTANT_DOMAIN, "config_entry_unique_id_collision_test2_group_2"),
    }

    await manager.async_remove(test2_group_2[0].entry_id)
    assert set(issue_registry.issues) == {
        (HOMEASSISTANT_DOMAIN, "config_entry_unique_id_collision_test2_group_2"),
    }

    # Remove the last test2 group2 duplicate, the issue is cleared
    await manager.async_remove(test2_group_2[1].entry_id)
    assert not issue_registry.issues
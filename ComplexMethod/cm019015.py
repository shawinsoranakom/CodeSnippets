async def test_async_listen_cloudhook_change(
    hass: HomeAssistant,
    cloud: MagicMock,
    set_cloud_prefs: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
) -> None:
    """Test async_listen_cloudhook_change."""
    assert await async_setup_component(hass, "cloud", {"cloud": {}})
    await hass.async_block_till_done()
    await cloud.login("test-user", "test-pass")

    webhook_id = "mock-webhook-id"
    cloudhook_url = "https://cloudhook.nabu.casa/abcdefg"

    # Set up initial cloudhooks state
    await set_cloud_prefs(
        {
            PREF_CLOUDHOOKS: {
                webhook_id: {
                    "webhook_id": webhook_id,
                    "cloudhook_id": "random-id",
                    "cloudhook_url": cloudhook_url,
                    "managed": True,
                }
            }
        }
    )

    # Track cloudhook changes
    changes = []
    changeInvoked = False

    def on_change(cloudhook: dict[str, Any] | None) -> None:
        """Handle cloudhook change."""
        nonlocal changeInvoked
        changes.append(cloudhook)
        changeInvoked = True

    # Register the change listener
    unsubscribe = async_listen_cloudhook_change(hass, webhook_id, on_change)

    # Verify no changes yet
    assert len(changes) == 0
    assert changeInvoked is False

    # Delete the cloudhook by updating prefs
    await set_cloud_prefs({PREF_CLOUDHOOKS: {}})
    await hass.async_block_till_done()

    # Verify deletion callback was called with None
    assert len(changes) == 1
    assert changes[-1] is None
    assert changeInvoked is True

    # Reset changeInvoked to detect next change
    changeInvoked = False

    # Add cloudhook back
    cloudhook_data = {
        "webhook_id": webhook_id,
        "cloudhook_id": "random-id",
        "cloudhook_url": cloudhook_url,
        "managed": True,
    }
    await set_cloud_prefs({PREF_CLOUDHOOKS: {webhook_id: cloudhook_data}})
    await hass.async_block_till_done()

    # Verify callback called with cloudhook data
    assert len(changes) == 2
    assert changes[-1] == cloudhook_data
    assert changeInvoked is True

    # Reset changeInvoked to detect next change
    changeInvoked = False

    # Update cloudhook data with same cloudhook should not trigger callback
    await set_cloud_prefs({PREF_CLOUDHOOKS: {webhook_id: cloudhook_data}})
    await hass.async_block_till_done()

    assert changeInvoked is False

    # Unsubscribe from listener
    unsubscribe()

    # Delete cloudhook again
    await set_cloud_prefs({PREF_CLOUDHOOKS: {}})
    await hass.async_block_till_done()

    # Verify change callback was NOT called after unsubscribe
    assert len(changes) == 2
    assert changeInvoked is False
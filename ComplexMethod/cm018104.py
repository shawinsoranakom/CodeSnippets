async def test_remove_expired_refresh_token(hass: HomeAssistant) -> None:
    """Test that expired refresh tokens are deleted."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    now = dt_util.utcnow()
    with freeze_time(now):
        refresh_token1 = await manager.async_create_refresh_token(user, CLIENT_ID)
        assert (
            refresh_token1.expire_at
            == now.timestamp() + timedelta(days=90).total_seconds()
        )

    with freeze_time(now + timedelta(days=30)):
        async_fire_time_changed(hass, now + timedelta(days=30))
        refresh_token2 = await manager.async_create_refresh_token(user, CLIENT_ID)
        assert (
            refresh_token2.expire_at
            == now.timestamp() + timedelta(days=120).total_seconds()
        )

    with freeze_time(now + timedelta(days=89, hours=23)):
        async_fire_time_changed(hass, now + timedelta(days=89, hours=23))
        await hass.async_block_till_done()
        assert manager.async_get_refresh_token(refresh_token1.id)
        assert manager.async_get_refresh_token(refresh_token2.id)

    with freeze_time(now + timedelta(days=90, seconds=5)):
        async_fire_time_changed(hass, now + timedelta(days=90, seconds=5))
        await hass.async_block_till_done()
        assert manager.async_get_refresh_token(refresh_token1.id) is None
        assert manager.async_get_refresh_token(refresh_token2.id)

    with freeze_time(now + timedelta(days=120, seconds=5)):
        async_fire_time_changed(hass, now + timedelta(days=120, seconds=5))
        await hass.async_block_till_done()
        assert manager.async_get_refresh_token(refresh_token1.id) is None
        assert manager.async_get_refresh_token(refresh_token2.id) is None
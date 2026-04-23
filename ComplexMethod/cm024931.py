async def test_reload_service_helper(hass: HomeAssistant) -> None:
    """Test the reload service helper."""

    active_reload_calls = 0
    service_error: type[Exception] | None = None
    reloaded = []

    async def reload_service_handler(service_call: ServiceCall) -> None:
        """Remove all automations and load new ones from config."""
        nonlocal active_reload_calls
        if service_error:
            raise service_error
        # Assert the reload helper prevents parallel reloads
        assert not active_reload_calls
        active_reload_calls += 1
        if not (target := service_call.data.get("target")):
            reloaded.append("all")
        else:
            reloaded.append(target)
        await asyncio.sleep(0.01)
        active_reload_calls -= 1

    def reload_targets(service_call: ServiceCall) -> set[str | None]:
        if target_id := service_call.data.get("target"):
            return {target_id}
        return {"target1", "target2", "target3", "target4"}

    # Test redundant reload of single targets
    reloader = service.ReloadServiceHelper(reload_service_handler, reload_targets)
    tasks = [
        # This reload task will start executing first, (target1)
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        # These reload tasks will be deduplicated to (target2, target3, target4, target1)
        # while the first task is reloaded, note that target1 can't be deduplicated
        # because it's already being reloaded.
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
    ]
    await asyncio.gather(*tasks)
    assert reloaded == unordered(
        ["target1", "target2", "target3", "target4", "target1"]
    )

    # Test redundant reload of multiple targets + single target
    reloaded.clear()
    tasks = [
        # This reload task will start executing first, (target1)
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        # These reload tasks will be deduplicated to (target2, target3, target4, all)
        # while the first task is reloaded.
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
        reloader.execute_service(ServiceCall(hass, "test", "test")),
    ]
    await asyncio.gather(*tasks)
    assert reloaded == unordered(["target1", "target2", "target3", "target4", "all"])

    # Test redundant reload of multiple targets + single target
    reloaded.clear()
    tasks = [
        # This reload task will start executing first, (all)
        reloader.execute_service(ServiceCall(hass, "test", "test")),
        # These reload tasks will be deduplicated to (target1, target2, target3, target4)
        # while the first task is reloaded.
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
    ]
    await asyncio.gather(*tasks)
    assert reloaded == unordered(["all", "target1", "target2", "target3", "target4"])

    # Test redundant reload of single targets
    reloaded.clear()
    tasks = [
        # This reload task will start executing first, (target1)
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        # These reload tasks will be deduplicated to (target2, target3, target4, target1)
        # while the first task is reloaded, note that target1 can't be deduplicated
        # because it's already being reloaded.
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
    ]
    await asyncio.gather(*tasks)
    assert reloaded == unordered(
        ["target1", "target2", "target3", "target4", "target1"]
    )

    # Test redundant reload of multiple targets + single target
    reloaded.clear()
    tasks = [
        # This reload task will start executing first, (target1)
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        # These reload tasks will be deduplicated to (target2, target3, target4, all)
        # while the first task is reloaded.
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
        reloader.execute_service(ServiceCall(hass, "test", "test")),
        reloader.execute_service(ServiceCall(hass, "test", "test")),
    ]
    await asyncio.gather(*tasks)
    assert reloaded == unordered(["target1", "target2", "target3", "target4", "all"])

    # Test redundant reload of multiple targets + single target
    reloaded.clear()
    tasks = [
        # This reload task will start executing first, (all)
        reloader.execute_service(ServiceCall(hass, "test", "test")),
        # These reload tasks will be deduplicated to (target1, target2, target3, target4)
        # while the first task is reloaded.
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
    ]
    await asyncio.gather(*tasks)
    assert reloaded == unordered(["all", "target1", "target2", "target3", "target4"])

    # Test error handling when reload fails, and that we can recover from it
    reloaded.clear()
    service_error = Exception("Test error")
    tasks = [
        # This reload task will start executing first, (all)
        reloader.execute_service(ServiceCall(hass, "test", "test")),
        # These reload tasks will be deduplicated to (target1, target2, target3, target4)
        # while the first task is reloaded.
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target2"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target3"})
        ),
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target4"})
        ),
    ]
    with pytest.raises(Exception, match="Test error"):
        await asyncio.gather(*tasks)
    assert reloaded == unordered([])

    service_error = None
    tasks2 = [
        reloader.execute_service(
            ServiceCall(hass, "test", "test", {"target": "target1"})
        ),
    ]
    await asyncio.gather(*tasks2)
    # We don't try to reload the failed targets again, so only the new reload is executed
    assert reloaded == unordered(["target1"])
async def hue_activate_scene_v1(
    bridge: HueBridge,
    group_name: str,
    scene_name: str,
    transition: int | None = None,
    is_retry: bool = False,
) -> bool:
    """Service for V1 bridge to call directly into bridge to set scenes."""
    api: HueBridgeV1 = bridge.api
    if api.scenes is None:
        LOGGER.warning("Hub %s does not support scenes", api.host)
        return False

    group = next(
        (group for group in api.groups.values() if group.name == group_name),
        None,
    )
    # Additional scene logic to handle duplicate scene names across groups
    scene = next(
        (
            scene
            for scene in api.scenes.values()
            if scene.name == scene_name
            and group is not None
            and sorted(scene.lights) == sorted(group.lights)
        ),
        None,
    )
    # If we can't find it, fetch latest info and try again
    if not is_retry and (group is None or scene is None):
        await bridge.async_request_call(api.groups.update)
        await bridge.async_request_call(api.scenes.update)
        return await hue_activate_scene_v1(
            bridge, group_name, scene_name, transition, is_retry=True
        )

    if group is None or scene is None:
        LOGGER.debug(
            "Unable to find scene %s for group %s on bridge %s",
            scene_name,
            group_name,
            bridge.host,
        )
        return False

    await bridge.async_request_call(
        group.set_action, scene=scene.id, transitiontime=transition
    )
    return True
def clean_actor() -> Generator[Callable[..., McpSessionActor], None, None]:
    """Fixture to track and clean up actors created in tests."""
    actors: list[McpSessionActor] = []

    def create_actor(*args: Any, **kwargs: Any) -> McpSessionActor:
        actor = McpSessionActor(*args, **kwargs)
        actors.append(actor)
        return actor

    yield create_actor

    # Clean up all actors
    for actor in actors:
        if hasattr(actor, "_active") and actor._active:  # type: ignore[reportPrivateUsage]
            try:
                # Try to close the actor properly
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(actor.close())
                else:
                    loop.run_until_complete(actor.close())
            except Exception:
                # If we can't close it properly, at least deactivate it
                actor._active = False  # type: ignore[reportPrivateUsage]
                if hasattr(actor, "_actor_task") and actor._actor_task:  # type: ignore[reportPrivateUsage]
                    actor._actor_task.cancel()
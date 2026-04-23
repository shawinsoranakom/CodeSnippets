def test_thread_status_to_str() -> None:
    """Test all values of this enum get a translatable string."""
    assert thread_status_to_str(ThreadStatus.BORDER_ROUTER) == "border_router"
    assert thread_status_to_str(ThreadStatus.LEADER) == "leader"
    assert thread_status_to_str(ThreadStatus.ROUTER) == "router"
    assert thread_status_to_str(ThreadStatus.CHILD) == "child"
    assert thread_status_to_str(ThreadStatus.JOINING) == "joining"
    assert thread_status_to_str(ThreadStatus.DETACHED) == "detached"
    assert thread_status_to_str(ThreadStatus.DISABLED) == "disabled"
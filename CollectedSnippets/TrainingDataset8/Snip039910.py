def _create_state_spy(
    initial_state_values: Dict[str, Any], disconnect: bool
) -> Tuple[SafeSessionState, Mock]:
    """Create a SafeSessionState, and return a Mock that
    spies on its underlying SessionState instance.
    """
    # SessionState is a "slotted" class, which makes it non-mockable.
    # The workaround is to create a subclass that is not slotted:
    # https://www.attrs.org/en/21.4.0.post1/glossary.html#term-slotted-classes
    class MockableSessionState(SessionState):
        pass

    # Create a SessionState instance and populate its values.
    session_state = MockableSessionState()
    for key, value in initial_state_values.items():
        session_state[key] = value

    # Create a "spy" mock that just wraps our session_state while letting
    # us observe calls. MagicMock does not implement dunder methods,
    # so we manually add them.
    # (See https://github.com/python/cpython/issues/69783)
    session_state_spy = MagicMock(spec=SessionState, wraps=session_state)
    session_state_spy.__getitem__ = Mock(wraps=session_state.__getitem__)
    session_state_spy.__setitem__ = Mock(wraps=session_state.__setitem__)
    session_state_spy.__delitem__ = Mock(wraps=session_state.__delitem__)
    session_state_spy.__iter__ = Mock(wraps=session_state.__iter__)
    session_state_spy.__len__ = Mock(wraps=session_state.__len__)

    safe_state = SafeSessionState(session_state_spy)
    if disconnect:
        safe_state.disconnect()

    return safe_state, session_state_spy
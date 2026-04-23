def test_is_callback_check_partial() -> None:
    """Test is_callback_check_partial matches HassJob."""

    @ha.callback
    def callback_func() -> None:
        pass

    def not_callback_func() -> None:
        pass

    assert ha.is_callback(callback_func)
    assert HassJob(callback_func).job_type == ha.HassJobType.Callback
    assert ha.is_callback_check_partial(functools.partial(callback_func))
    assert HassJob(functools.partial(callback_func)).job_type == ha.HassJobType.Callback
    assert ha.is_callback_check_partial(
        functools.partial(functools.partial(callback_func))
    )
    assert HassJob(functools.partial(functools.partial(callback_func))).job_type == (
        ha.HassJobType.Callback
    )
    assert not ha.is_callback_check_partial(not_callback_func)
    assert HassJob(not_callback_func).job_type == ha.HassJobType.Executor
    assert not ha.is_callback_check_partial(functools.partial(not_callback_func))
    assert HassJob(functools.partial(not_callback_func)).job_type == (
        ha.HassJobType.Executor
    )

    # We check the inner function, not the outer one
    assert not ha.is_callback_check_partial(
        ha.callback(functools.partial(not_callback_func))
    )
    assert HassJob(ha.callback(functools.partial(not_callback_func))).job_type == (
        ha.HassJobType.Executor
    )
def opcheck(
    op: torch._ops.OpOverload | torch._ops.OpOverloadPacket | CustomOpDef,
    args: tuple[Any, ...],
    kwargs: dict[str, Any] | None = None,
    *,
    test_utils: str | Sequence[str] = DEFAULT_TEST_UTILS,
    raise_exception: bool = True,
    rtol: float | None = None,
    atol: float | None = None,
) -> dict[str, str]:
    """See torch.library.opcheck for docstring"""

    if (rtol is None) ^ (atol is None):
        raise ValueError(
            "opcheck(op, ...): if you specify one of rtol/atol, you must specify both"
        )

    if kwargs is None:
        kwargs = {}
    if isinstance(op, CustomOpDef):
        op = op._opoverload
    if isinstance(op, torch._ops.OpOverloadPacket):
        op = resolve_unique_overload_or_throw(op)
    if not isinstance(op, torch._ops.OpOverload):
        raise ValueError(
            f"opcheck(op, ...): op must be instance of torch._ops.OpOverload, "
            f"e.g. torch.ops.aten.sin.default, got {type(op)}"
        )
    if test_utils == "ALL":
        test_utils = tuple(ALL_TEST_UTILS.keys())
    if isinstance(test_utils, str):
        test_utils = (test_utils,)
    if not isinstance(test_utils, (tuple, list)) or not set(test_utils).issubset(
        ALL_TEST_UTILS.keys()
    ):
        raise ValueError(
            f"opcheck(op, ..., test_utils={test_utils}), expected test_utils "
            f"to be subset of {tuple(ALL_TEST_UTILS.keys())} but it was not"
        )

    results_dict = {}
    for test_util in test_utils:
        tester = ALL_TEST_UTILS[test_util]
        try:
            tester(op, args, kwargs, rtol=rtol, atol=atol)
            results_dict[test_util] = "SUCCESS"
        except Exception as ex:
            if raise_exception:
                raise OpCheckError(
                    f"opcheck(op, ...): {test_util} failed with {ex} "
                    f"(scroll up for stack trace)"
                ) from ex
            results_dict[test_util] = ex
    return results_dict
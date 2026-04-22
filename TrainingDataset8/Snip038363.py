def _fix_tornado_crash() -> None:
    """Set default asyncio policy to be compatible with Tornado 6.

    Tornado 6 (at least) is not compatible with the default
    asyncio implementation on Windows. So here we
    pick the older SelectorEventLoopPolicy when the OS is Windows
    if the known-incompatible default policy is in use.

    This has to happen as early as possible to make it a low priority and
    overridable

    See: https://github.com/tornadoweb/tornado/issues/2608

    FIXME: if/when tornado supports the defaults in asyncio,
    remove and bump tornado requirement for py38
    """
    if env_util.IS_WINDOWS and sys.version_info >= (3, 8):
        try:
            from asyncio import (  # type: ignore[attr-defined]
                WindowsProactorEventLoopPolicy,
                WindowsSelectorEventLoopPolicy,
            )
        except ImportError:
            pass
            # Not affected
        else:
            if type(asyncio.get_event_loop_policy()) is WindowsProactorEventLoopPolicy:
                # WindowsProactorEventLoopPolicy is not compatible with
                # Tornado 6 fallback to the pre-3.8 default of Selector
                asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
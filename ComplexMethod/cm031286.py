def __getattr__(name: str):
    import warnings

    match name:
        case "AbstractEventLoopPolicy":
            warnings._deprecated(f"asyncio.{name}", remove=(3, 16))
            return events._AbstractEventLoopPolicy
        case "DefaultEventLoopPolicy":
            warnings._deprecated(f"asyncio.{name}", remove=(3, 16))
            if sys.platform == 'win32':
                return windows_events._DefaultEventLoopPolicy
            return unix_events._DefaultEventLoopPolicy
        case "WindowsSelectorEventLoopPolicy":
            if sys.platform == 'win32':
                warnings._deprecated(f"asyncio.{name}", remove=(3, 16))
                return windows_events._WindowsSelectorEventLoopPolicy
            # Else fall through to the AttributeError below.
        case "WindowsProactorEventLoopPolicy":
            if sys.platform == 'win32':
                warnings._deprecated(f"asyncio.{name}", remove=(3, 16))
                return windows_events._WindowsProactorEventLoopPolicy
            # Else fall through to the AttributeError below.

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
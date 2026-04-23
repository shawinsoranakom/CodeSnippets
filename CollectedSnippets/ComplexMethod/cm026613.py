def protected_getattr(obj: object, name: str, default: Any = None) -> Any:
        """Restricted method to get attributes."""
        if name.startswith("async_"):
            raise ScriptError("Not allowed to access async methods")
        if (
            (obj is hass and name not in ALLOWED_HASS)
            or (obj is hass.bus and name not in ALLOWED_EVENTBUS)
            or (obj is hass.states and name not in ALLOWED_STATEMACHINE)
            or (obj is hass.services and name not in ALLOWED_SERVICEREGISTRY)
            or (obj is dt_util and name not in ALLOWED_DT_UTIL)
            or (obj is datetime and name not in ALLOWED_DATETIME)
            or (isinstance(obj, TimeWrapper) and name not in ALLOWED_TIME)
        ):
            raise ScriptError(f"Not allowed to access {obj.__class__.__name__}.{name}")

        return getattr(obj, name, default)
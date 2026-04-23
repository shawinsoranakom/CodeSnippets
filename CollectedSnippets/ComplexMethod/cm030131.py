def __new__(mcls, name, bases, namespace, /, **kwargs):
        if name == "Protocol" and bases == (Generic,):
            pass
        elif Protocol in bases:
            for base in bases:
                if not (
                    base in {object, Generic}
                    or base.__name__ in _PROTO_ALLOWLIST.get(base.__module__, [])
                    or (
                        issubclass(base, Generic)
                        and getattr(base, "_is_protocol", False)
                    )
                ):
                    raise TypeError(
                        f"Protocols can only inherit from other protocols, "
                        f"got {base!r}"
                    )
        return super().__new__(mcls, name, bases, namespace, **kwargs)
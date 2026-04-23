def __new__(metacls, name, bases, attrs):
        if bases:
            if "check" in attrs or "_check_graph_module" in attrs:
                raise SyntaxError("Overriding method check is not allowed.")
            if "dialect" not in attrs or attrs["dialect"] == "ATEN":
                raise AssertionError(
                    f"subclass must define dialect != 'ATEN', got {attrs.get('dialect')}"
                )
        else:
            if "check" not in attrs:
                raise AssertionError("base class must define 'check' method")
            if "_check_graph_module" not in attrs:
                raise AssertionError(
                    "base class must define '_check_graph_module' method"
                )
            if attrs["dialect"] != "ATEN":
                raise AssertionError(
                    f"base class dialect must be 'ATEN', got {attrs['dialect']}"
                )

        if not isinstance(attrs["dialect"], str):
            raise AssertionError(f"dialect must be str, got {type(attrs['dialect'])}")
        ret = type.__new__(metacls, name, bases, attrs)
        metacls._registry[attrs["dialect"]] = ret  # type: ignore[assignment]
        return ret
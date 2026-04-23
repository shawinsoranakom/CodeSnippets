def __new__(mcs: type["PluginMeta"], *args: Any, **kwargs: Any) -> "PluginMeta":
        """Create a new instance of the class."""
        name, bases, attrs = args
        indicators: dict[str, Indicator] = {}
        cls_attrs: dict[str, list] = {
            "__ma_mode__": [],
            "__inchart__": [],
            "__subplots__": [],
        }
        new_cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        for base in reversed(new_cls.__mro__):
            for elem, value in base.__dict__.items():
                if elem in indicators:
                    del indicators[elem]

                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__  # noqa: PLW2901
                if isinstance(value, Indicator):
                    if is_static_method:
                        raise TypeError(
                            f"Indicator {value.name} can't be a static method"
                        )
                    indicators[value.name] = value
                elif is_static_method and elem not in new_cls.__static_methods__:
                    new_cls.__static_methods__.append(elem)

                if elem in ["__ma_mode__", "__inchart__", "__subplots__"]:
                    cls_attrs[elem].extend(value)

        new_cls.__indicators__ = list(indicators.values())
        new_cls.__static_methods__ = list(set(new_cls.__static_methods__))
        new_cls.__ma_mode__ = list(set(cls_attrs["__ma_mode__"]))
        new_cls.__inchart__ = list(set(cls_attrs["__inchart__"]))
        new_cls.__subplots__ = list(set(cls_attrs["__subplots__"]))

        return new_cls
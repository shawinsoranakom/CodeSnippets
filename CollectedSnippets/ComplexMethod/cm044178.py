def __new__(cls, *args: Any, **kwargs: Any) -> "PltTA":
        """Create a new instance of the class."""
        if cls is PltTA:
            raise TypeError("Can't instantiate abstract class Plugin directly")
        self = super().__new__(cls)

        static_methods = cls.__static_methods__
        indicators = cls.__indicators__

        for item in indicators:
            # we make sure that the indicator is bound to the instance
            if not hasattr(self, item.name):
                setattr(self, item.name, item.func.__get__(self, cls))

        for static_method in static_methods:
            if not hasattr(self, static_method):
                setattr(self, static_method, staticmethod(getattr(self, static_method)))

        for attr, value in cls.__dict__.items():
            if attr in [
                "__ma_mode__",
                "__inchart__",
                "__subplots__",
            ] and value not in getattr(self, attr):
                getattr(self, attr).extend(value)

        return self
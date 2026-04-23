def add_plugins(self, plugins: list["PltTA"]) -> None:
        """Add plugins to current instance."""
        for plugin in plugins:
            for item in plugin.__indicators__:
                # pylint: disable=unnecessary-dunder-call
                if not hasattr(self, item.name):
                    setattr(self, item.name, item.func.__get__(self, type(self)))
                    self.__indicators__.append(item)

            for static_method in plugin.__static_methods__:
                if not hasattr(self, static_method):
                    setattr(
                        self, static_method, staticmethod(getattr(self, static_method))
                    )
            for attr, value in plugin.__dict__.items():
                if attr in [
                    "__ma_mode__",
                    "__inchart__",
                    "__subplots__",
                ] and value not in getattr(self, attr):
                    getattr(self, attr).extend(value)
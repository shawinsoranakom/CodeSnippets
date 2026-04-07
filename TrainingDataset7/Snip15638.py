def __dir__(self):
        return super().__dir__() + dir(global_settings) + ["FOO"]
def from_parameter(cls, config):
        if config is None or isinstance(config, cls):
            return config
        return cls(config)
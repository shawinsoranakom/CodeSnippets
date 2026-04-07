def _databases_names(cls, include_mirrors=True):
        # Only consider allowed database aliases, including mirrors or not.
        return [
            alias
            for alias in connections
            if alias in cls.databases
            and (
                include_mirrors
                or not connections[alias].settings_dict["TEST"]["MIRROR"]
            )
        ]
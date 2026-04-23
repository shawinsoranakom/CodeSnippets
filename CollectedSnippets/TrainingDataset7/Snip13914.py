def _databases_support_savepoints(cls):
        return connections_support_savepoints(cls.databases)
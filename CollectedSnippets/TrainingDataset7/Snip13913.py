def _databases_support_transactions(cls):
        return connections_support_transactions(cls.databases)
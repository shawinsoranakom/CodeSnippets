def tearDownClass(cls):
        if (
            cls._databases_support_transactions()
            and cls._databases_support_savepoints()
        ):
            cls._rollback_atomics(cls.cls_atomics)
            for conn in connections.all(initialized_only=True):
                conn.close()
        super().tearDownClass()
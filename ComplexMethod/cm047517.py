def __new__(cls, cr: BaseCursor, uid: int, context: dict, su: bool = False):
        assert isinstance(cr, BaseCursor)
        if uid == SUPERUSER_ID:
            su = True

        # determine transaction object
        transaction = cr.transaction
        if transaction is None:
            transaction = cr.transaction = Transaction(Registry(cr.dbname))

        # if env already exists, return it
        for env in transaction.envs:
            if env.cr is cr and env.uid == uid and env.su == su and env.context == context:
                return env

        # otherwise create environment, and add it in the set
        self = object.__new__(cls)
        self.cr, self.uid, self.su = cr, uid, su
        self.context = frozendict(context)
        self.transaction = transaction

        transaction.envs.add(self)
        # the default transaction's environment is the first one with a valid uid
        if transaction.default_env is None and uid and isinstance(uid, int):
            transaction.default_env = self
        return self
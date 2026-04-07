def setUpClass(cls):
        cls._lockfile = open(cls.lockfile)
        cls.addClassCleanup(cls._lockfile.close)
        locks.lock(cls._lockfile, locks.LOCK_EX)
        super().setUpClass()
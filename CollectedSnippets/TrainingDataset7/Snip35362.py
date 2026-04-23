def setUpClass(cls):
        try:
            super().setUpClass()
        except cls.MyException:
            cls._in_atomic_block = connection.in_atomic_block
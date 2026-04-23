def setUpClass(cls):
        super().setUpClass()
        if not issubclass(cls, TestCase):
            cls._pre_setup()
            cls._pre_setup_ran_eagerly = True
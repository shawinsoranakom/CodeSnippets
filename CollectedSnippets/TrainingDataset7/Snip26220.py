def setUp(self):
        super().setUp()
        self.__stdout = sys.stdout
        self.stream = sys.stdout = StringIO()
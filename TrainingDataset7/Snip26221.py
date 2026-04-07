def tearDown(self):
        del self.stream
        sys.stdout = self.__stdout
        del self.__stdout
        super().tearDown()
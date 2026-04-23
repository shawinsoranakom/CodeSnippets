def addSubTest(self, test, subtest, err):
        if err is not None:
            self.debug(err)
        super().addSubTest(test, subtest, err)
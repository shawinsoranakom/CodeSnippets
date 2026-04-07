def runTest(self):
            with self.subTest():
                Person.objects.filter(first_name="subtest-error").count()
                raise Exception
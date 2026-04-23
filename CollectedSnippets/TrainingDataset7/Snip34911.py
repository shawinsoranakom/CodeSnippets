def runTest(self):
            Person.objects.filter(first_name="fail").count()
            self.fail()
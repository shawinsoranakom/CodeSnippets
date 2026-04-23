def runTest(self):
            Person.objects.filter(first_name="error").count()
            raise Exception
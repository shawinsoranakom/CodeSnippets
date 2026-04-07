def setUpTestData(cls):
        boss = Employee.objects.create(name="Peter")
        Employee.objects.create(name="Joe", boss=boss)
        Employee.objects.create(name="Angela", boss=boss)
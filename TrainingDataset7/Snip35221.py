def setUpTestData(cls):
        cls.person_pk = str(Person.objects.create(name="test").pk)
        cls.url = f"/test_utils/get_person/{cls.person_pk}/"
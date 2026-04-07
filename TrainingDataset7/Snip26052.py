def setUpTestData(cls):
        cls.dad = Person.objects.create(
            full_name="John Smith Senior", mother=None, father=None
        )
        cls.mom = Person.objects.create(
            full_name="Jane Smith", mother=None, father=None
        )
        cls.kid = Person.objects.create(
            full_name="John Smith Junior", mother=cls.mom, father=cls.dad
        )
def setUpTestData(cls):
        cls.bob = Person.objects.create(name="Bob")
        cls.roll = Group.objects.create(name="Roll")
        cls.bob_roll = Membership.objects.create(person=cls.bob, group=cls.roll)
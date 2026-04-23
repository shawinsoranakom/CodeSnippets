def setUpTestData(cls):
        cls.bob = Person.objects.create(name="Bob")
        cls.jim = Person.objects.create(name="Jim")

        cls.rock = Group.objects.create(name="Rock")
        cls.roll = Group.objects.create(name="Roll")

        cls.frank = User.objects.create_user("frank", "frank@example.com", "password")
        cls.jane = User.objects.create_user("jane", "jane@example.com", "password")

        # normal intermediate model
        cls.bob_rock = Membership.objects.create(person=cls.bob, group=cls.rock)
        cls.bob_roll = Membership.objects.create(
            person=cls.bob, group=cls.roll, price=50
        )
        cls.jim_rock = Membership.objects.create(
            person=cls.jim, group=cls.rock, price=50
        )

        # intermediate model with custom id column
        cls.frank_rock = UserMembership.objects.create(user=cls.frank, group=cls.rock)
        cls.frank_roll = UserMembership.objects.create(user=cls.frank, group=cls.roll)
        cls.jane_rock = UserMembership.objects.create(user=cls.jane, group=cls.rock)
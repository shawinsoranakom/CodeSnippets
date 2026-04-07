def setUpTestData(cls):
        for i in range(1, 3):
            group = Group.objects.create(name="Group {}".format(i))
        cls.e1 = Event.objects.create(title="Event 1", group=group)
def setUpTestData(cls):
        cls.threepwood = Character.objects.create(
            username="threepwood",
            last_action=datetime.datetime.today() + datetime.timedelta(days=1),
        )
        cls.marley = Character.objects.create(
            username="marley",
            last_action=datetime.datetime.today() - datetime.timedelta(days=1),
        )
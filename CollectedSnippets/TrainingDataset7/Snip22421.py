def setUpTestData(cls):
        # Creating countries
        cls.usa = Country.objects.create(name="United States of America")
        cls.soviet_union = Country.objects.create(name="Soviet Union")
        # Creating People
        cls.bob = Person.objects.create(name="Bob", person_country=cls.usa)
        cls.jim = Person.objects.create(name="Jim", person_country=cls.usa)
        cls.george = Person.objects.create(name="George", person_country=cls.usa)

        cls.jane = Person.objects.create(name="Jane", person_country=cls.soviet_union)
        cls.mark = Person.objects.create(name="Mark", person_country=cls.soviet_union)
        cls.sam = Person.objects.create(name="Sam", person_country=cls.soviet_union)

        # Creating Groups
        cls.kgb = Group.objects.create(name="KGB", group_country=cls.soviet_union)
        cls.cia = Group.objects.create(name="CIA", group_country=cls.usa)
        cls.republican = Group.objects.create(name="Republican", group_country=cls.usa)
        cls.democrat = Group.objects.create(name="Democrat", group_country=cls.usa)
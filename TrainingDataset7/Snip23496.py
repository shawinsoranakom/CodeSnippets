def setUpTestData(cls):
        cls.lion = Animal.objects.create(common_name="Lion", latin_name="Panthera leo")
        cls.platypus = Animal.objects.create(
            common_name="Platypus",
            latin_name="Ornithorhynchus anatinus",
        )
        Vegetable.objects.create(name="Eggplant", is_yucky=True)
        cls.bacon = Vegetable.objects.create(name="Bacon", is_yucky=False)
        cls.quartz = Mineral.objects.create(name="Quartz", hardness=7)

        # Tagging stuff.
        cls.fatty = cls.bacon.tags.create(tag="fatty")
        cls.salty = cls.bacon.tags.create(tag="salty")
        cls.yellow = cls.lion.tags.create(tag="yellow")
        cls.hairy = cls.lion.tags.create(tag="hairy")
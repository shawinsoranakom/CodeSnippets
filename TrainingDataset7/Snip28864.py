def test_metaclass_can_access_attribute_dict(self):
        """
        Model metaclasses have access to the class attribute dict in
        __init__() (#30254).
        """

        class HorseBase(models.base.ModelBase):
            def __init__(cls, name, bases, attrs):
                super().__init__(name, bases, attrs)
                cls.horns = 1 if "magic" in attrs else 0

        class Horse(models.Model, metaclass=HorseBase):
            name = models.CharField(max_length=255)
            magic = True

        self.assertEqual(Horse.horns, 1)
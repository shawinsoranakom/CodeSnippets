def test_invalid_definition(self):
        msg = "'str' object cannot be interpreted as an integer"
        with self.assertRaisesMessage(TypeError, msg):

            class InvalidArgumentEnum(models.IntegerChoices):
                # A string is not permitted as the second argument to int().
                ONE = 1, "X", "Invalid"

        msg = "duplicate values found in <enum 'Fruit'>: PINEAPPLE -> APPLE"
        with self.assertRaisesMessage(ValueError, msg):

            class Fruit(models.IntegerChoices):
                APPLE = 1, "Apple"
                PINEAPPLE = 1, "Pineapple"
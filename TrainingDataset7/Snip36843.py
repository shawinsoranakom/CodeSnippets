def test_basic_equality(self):
        self.assertEqual(
            MaxValueValidator(44),
            MaxValueValidator(44),
        )
        self.assertEqual(MaxValueValidator(44), mock.ANY)
        self.assertEqual(
            StepValueValidator(0.003),
            StepValueValidator(0.003),
        )
        self.assertNotEqual(
            MaxValueValidator(44),
            MinValueValidator(44),
        )
        self.assertNotEqual(
            MinValueValidator(45),
            MinValueValidator(11),
        )
        self.assertNotEqual(
            StepValueValidator(3),
            StepValueValidator(2),
        )
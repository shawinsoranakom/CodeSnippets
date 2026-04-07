def test_lazy_choices(self):
        class Model(models.Model):
            field = models.CharField(
                max_length=10, choices=lazy(lambda: [[1, "1"], [2, "2"]], tuple)()
            )

        self.assertEqual(Model._meta.get_field("field").check(), [])
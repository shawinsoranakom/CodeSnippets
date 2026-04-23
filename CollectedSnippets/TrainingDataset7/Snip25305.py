def test_pointing_to_fk(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            foo_1 = models.ForeignKey(
                Foo, on_delete=models.CASCADE, related_name="bar_1"
            )
            foo_2 = models.ForeignKey(
                Foo, on_delete=models.CASCADE, related_name="bar_2"
            )

            class Meta:
                unique_together = [["foo_1_id", "foo_2"]]

        self.assertEqual(Bar.check(), [])
def test_unique_together_normalization(self):
        """
        Test the Meta.unique_together normalization with different sorts of
        objects.
        """
        data = {
            "2-tuple": (("foo", "bar"), (("foo", "bar"),)),
            "list": (["foo", "bar"], (("foo", "bar"),)),
            "already normalized": (
                (("foo", "bar"), ("bar", "baz")),
                (("foo", "bar"), ("bar", "baz")),
            ),
            "set": (
                {("foo", "bar"), ("bar", "baz")},  # Ref #21469
                (("foo", "bar"), ("bar", "baz")),
            ),
        }

        for unique_together, normalized in data.values():

            class M(models.Model):
                foo = models.IntegerField()
                bar = models.IntegerField()
                baz = models.IntegerField()

                Meta = type(
                    "Meta", (), {"unique_together": unique_together, "apps": Apps()}
                )

            checks, _ = M()._get_unique_checks()
            for t in normalized:
                check = (M, t)
                self.assertIn(check, checks)
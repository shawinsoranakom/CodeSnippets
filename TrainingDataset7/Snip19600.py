def test_filter_and_count_user_by_pk(self):
        test_cases = (
            ({"pk": self.user_1.pk}, 1),
            ({"pk": self.user_2.pk}, 1),
            ({"pk": self.user_3.pk}, 1),
            ({"pk": (self.tenant_1.id, self.user_1.id)}, 1),
            ({"pk": (self.tenant_1.id, self.user_2.id)}, 1),
            ({"pk": (self.tenant_2.id, self.user_3.id)}, 1),
            ({"pk": (self.tenant_1.id, self.user_3.id)}, 0),
            ({"pk": (self.tenant_2.id, self.user_1.id)}, 0),
            ({"pk": (self.tenant_2.id, self.user_2.id)}, 0),
        )

        for lookup, count in test_cases:
            with self.subTest(lookup=lookup, count=count):
                self.assertEqual(User.objects.filter(**lookup).count(), count)
def test_no_delete(self):
        """Verify base formset doesn't modify database"""
        # reload database
        self.test_init_database()

        # pass standard data dict & see none updated
        data = dict(self.data)
        data["form-INITIAL_FORMS"] = 4
        data.update(
            {
                "form-%d-id" % i: user.pk
                for i, user in enumerate(User.objects.order_by("pk"))
            }
        )
        formset = self.NormalFormset(data, queryset=User.objects.all())
        self.assertTrue(formset.is_valid())
        self.assertEqual(len(formset.save()), 0)
        self.assertEqual(len(User.objects.all()), 4)
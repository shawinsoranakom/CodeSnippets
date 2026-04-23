def test_all_delete(self):
        """Verify base formset honors DELETE field"""
        # reload database
        self.test_init_database()

        # create data dict with all fields marked for deletion
        data = dict(self.data)
        data["form-INITIAL_FORMS"] = 4
        data.update(
            {"form-%d-id" % i: user.pk for i, user in enumerate(User.objects.all())}
        )
        data.update(self.delete_all_ids)
        formset = self.NormalFormset(data, queryset=User.objects.all())
        self.assertTrue(formset.is_valid())
        self.assertEqual(len(formset.save()), 0)
        self.assertEqual(len(User.objects.all()), 0)
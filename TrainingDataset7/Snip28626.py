def test_custom_delete(self):
        """Verify DeleteFormset ignores DELETE field and uses form method"""
        # reload database
        self.test_init_database()

        # Create formset with custom Delete function
        # create data dict with all fields marked for deletion
        data = dict(self.data)
        data["form-INITIAL_FORMS"] = 4
        data.update(
            {
                "form-%d-id" % i: user.pk
                for i, user in enumerate(User.objects.order_by("pk"))
            }
        )
        data.update(self.delete_all_ids)
        formset = self.DeleteFormset(data, queryset=User.objects.all())

        # Three with odd serial values were deleted.
        self.assertTrue(formset.is_valid())
        self.assertEqual(len(formset.save()), 0)
        self.assertEqual(User.objects.count(), 1)

        # No odd serial values left.
        odd_serials = [user.serial for user in User.objects.all() if user.serial % 2]
        self.assertEqual(len(odd_serials), 0)
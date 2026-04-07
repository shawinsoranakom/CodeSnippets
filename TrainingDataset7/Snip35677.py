def test_update_non_concrete_field(self):
        profile_boss = Profile.objects.create(name="Boss", salary=3000)
        with self.assertRaisesMessage(ValueError, self.msg % "non_concrete"):
            profile_boss.save(update_fields=["non_concrete"])
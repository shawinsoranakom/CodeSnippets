def test_many_to_many_through_isolate_apps_model(self):
        """
        #25723 - Through model registration lookup should be run against the
        field's model registry.
        """

        class GroupMember(models.Model):
            person = models.ForeignKey("Person", models.CASCADE)
            group = models.ForeignKey("Group", models.CASCADE)

        class Person(models.Model):
            pass

        class Group(models.Model):
            members = models.ManyToManyField("Person", through="GroupMember")

        field = Group._meta.get_field("members")
        self.assertEqual(field.check(from_model=Group), [])
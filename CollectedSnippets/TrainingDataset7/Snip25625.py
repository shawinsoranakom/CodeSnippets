def test_explicit_field_names(self):
        """
        If ``through_fields`` kwarg is given, it must specify both
        link fields of the intermediary table.
        """

        class Fan(models.Model):
            pass

        class Event(models.Model):
            invitees = models.ManyToManyField(
                Fan, through="Invitation", through_fields=(None, "invitee")
            )

        class Invitation(models.Model):
            event = models.ForeignKey(Event, models.CASCADE)
            invitee = models.ForeignKey(Fan, models.CASCADE)
            inviter = models.ForeignKey(Fan, models.CASCADE, related_name="+")

        field = Event._meta.get_field("invitees")
        self.assertEqual(
            field.check(from_model=Event),
            [
                Error(
                    "Field specifies 'through_fields' but does not provide the names "
                    "of the two link fields that should be used for the relation "
                    "through model 'invalid_models_tests.Invitation'.",
                    hint=(
                        "Make sure you specify 'through_fields' as "
                        "through_fields=('field1', 'field2')"
                    ),
                    obj=field,
                    id="fields.E337",
                ),
            ],
        )
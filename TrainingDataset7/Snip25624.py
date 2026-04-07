def test_invalid_field(self):
        """
        Providing invalid field names to ManyToManyField.through_fields
        triggers validation errors.
        """

        class Fan(models.Model):
            pass

        class Event(models.Model):
            invitees = models.ManyToManyField(
                Fan,
                through="Invitation",
                through_fields=("invalid_field_1", "invalid_field_2"),
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
                    "The intermediary model 'invalid_models_tests.Invitation' has no "
                    "field 'invalid_field_1'.",
                    hint=(
                        "Did you mean one of the following foreign keys to 'Event': "
                        "event?"
                    ),
                    obj=field,
                    id="fields.E338",
                ),
                Error(
                    "The intermediary model 'invalid_models_tests.Invitation' has no "
                    "field 'invalid_field_2'.",
                    hint=(
                        "Did you mean one of the following foreign keys to 'Fan': "
                        "invitee, inviter?"
                    ),
                    obj=field,
                    id="fields.E338",
                ),
            ],
        )
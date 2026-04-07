def test_contribute_to_class(self):
        class BareModel(Model):
            pass

        new_field = GeneratedField(
            expression=Lower("nonexistent"),
            output_field=IntegerField(),
            db_persist=True,
        )
        apps.models_ready = False
        try:
            # GeneratedField can be added to the model even when apps are not
            # fully loaded.
            new_field.contribute_to_class(BareModel, "name")
            self.assertEqual(BareModel._meta.get_field("name"), new_field)
        finally:
            apps.models_ready = True
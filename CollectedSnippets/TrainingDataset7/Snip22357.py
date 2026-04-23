def test_force_update_on_inherited_model_without_fields(self):
        """
        Issue 13864: force_update fails on subclassed models, if they don't
        specify custom fields.
        """
        a = SubCounter(name="count", value=1)
        a.save()
        a.value = 2
        a.save(force_update=True)
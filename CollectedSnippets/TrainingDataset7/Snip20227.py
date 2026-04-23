def test_deconstruct_from_queryset_failing(self):
        mgr = CustomManager("arg")
        msg = (
            "Could not find manager BaseCustomManagerFromCustomQuerySet in "
            "django.db.models.manager.\n"
            "Please note that you need to inherit from managers you "
            "dynamically generated with 'from_queryset()'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            mgr.deconstruct()
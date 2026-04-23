def test_db_setdefault_none(self):
        # Object cannot be created on the module initialization, use hardcoded
        # PKs instead.
        r = RelatedDbOptionParent.objects.create(pk=2)
        default_r = RelatedDbOptionParent.objects.create(pk=1)
        set_default_db_obj = SetDefaultDbModel.objects.create(
            db_setdefault_none=r, db_setdefault=default_r
        )
        set_default_db_obj.db_setdefault_none.delete()
        set_default_db_obj = SetDefaultDbModel.objects.get(pk=set_default_db_obj.pk)
        self.assertIsNone(set_default_db_obj.db_setdefault_none)
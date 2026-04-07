def test_db_setdefault(self):
        # Object cannot be created on the module initialization, use hardcoded
        # PKs instead.
        r = RelatedDbOptionParent.objects.create(pk=2)
        default_r = RelatedDbOptionParent.objects.create(pk=1)
        set_default_db_obj = SetDefaultDbModel.objects.create(db_setdefault=r)
        set_default_db_obj.db_setdefault.delete()
        set_default_db_obj = SetDefaultDbModel.objects.get(pk=set_default_db_obj.pk)
        self.assertEqual(set_default_db_obj.db_setdefault, default_r)
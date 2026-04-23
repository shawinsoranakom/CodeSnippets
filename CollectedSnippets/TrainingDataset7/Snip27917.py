def test_generated_fields_can_be_deferred(self):
        fk_object = Foo.objects.create(a="abc", d=Decimal("12.34"))
        m = self.base_model.objects.create(a=1, b=2, fk=fk_object)
        m = self.base_model.objects.defer("field").get(id=m.id)
        self.assertEqual(m.get_deferred_fields(), {"field"})
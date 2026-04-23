def test_lefthand_transformed_field_bitwise_or(self):
        Employee.objects.create(firstname="Max", lastname="Mustermann")
        with register_lookup(CharField, Length):
            qs = Employee.objects.annotate(bitor=F("lastname__length").bitor(48))
            self.assertEqual(qs.get().bitor, 58)
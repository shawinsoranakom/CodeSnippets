def test_output_field_decimalfield(self):
        Time.objects.create()
        time = Time.objects.annotate(one=Value(1, output_field=DecimalField())).first()
        self.assertEqual(time.one, 1)
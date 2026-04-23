def test_case_when_db_default_no_returning(self):
        m = DBDefaultsFunction.objects.create()
        m.refresh_from_db()
        self.assertEqual(m.case_when, 3)
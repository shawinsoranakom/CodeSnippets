def test_ticket_23270(self):
        d = Derived.objects.create(text="foo", other_text="bar")
        with self.assertNumQueries(1):
            obj = Base.objects.select_related("derived").defer("text")[0]
            self.assertIsInstance(obj.derived, Derived)
            self.assertEqual("bar", obj.derived.other_text)
            self.assertNotIn("text", obj.__dict__)
            self.assertEqual(d.pk, obj.derived.base_ptr_id)
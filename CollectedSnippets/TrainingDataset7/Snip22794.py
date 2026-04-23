def test_explicit_field_order(self):
        class TestFormParent(Form):
            field1 = CharField()
            field2 = CharField()
            field4 = CharField()
            field5 = CharField()
            field6 = CharField()
            field_order = ["field6", "field5", "field4", "field2", "field1"]

        class TestForm(TestFormParent):
            field3 = CharField()
            field_order = ["field2", "field4", "field3", "field5", "field6"]

        class TestFormRemove(TestForm):
            field1 = None

        class TestFormMissing(TestForm):
            field_order = ["field2", "field4", "field3", "field5", "field6", "field1"]
            field1 = None

        class TestFormInit(TestFormParent):
            field3 = CharField()
            field_order = None

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.order_fields(field_order=TestForm.field_order)

        p = TestFormParent()
        self.assertEqual(list(p.fields), TestFormParent.field_order)
        p = TestFormRemove()
        self.assertEqual(list(p.fields), TestForm.field_order)
        p = TestFormMissing()
        self.assertEqual(list(p.fields), TestForm.field_order)
        p = TestForm()
        self.assertEqual(list(p.fields), TestFormMissing.field_order)
        p = TestFormInit()
        order = [*TestForm.field_order, "field1"]
        self.assertEqual(list(p.fields), order)
        TestForm.field_order = ["unknown"]
        p = TestForm()
        self.assertEqual(
            list(p.fields), ["field1", "field2", "field4", "field5", "field6", "field3"]
        )
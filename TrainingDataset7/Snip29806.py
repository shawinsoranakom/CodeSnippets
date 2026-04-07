def test_field_has_changed(self):
        class HStoreFormTest(Form):
            f1 = forms.HStoreField()

        form_w_hstore = HStoreFormTest()
        self.assertFalse(form_w_hstore.has_changed())

        form_w_hstore = HStoreFormTest({"f1": '{"a": 1}'})
        self.assertTrue(form_w_hstore.has_changed())

        form_w_hstore = HStoreFormTest({"f1": '{"a": 1}'}, initial={"f1": '{"a": 1}'})
        self.assertFalse(form_w_hstore.has_changed())

        form_w_hstore = HStoreFormTest({"f1": '{"a": 2}'}, initial={"f1": '{"a": 1}'})
        self.assertTrue(form_w_hstore.has_changed())

        form_w_hstore = HStoreFormTest({"f1": '{"a": 1}'}, initial={"f1": {"a": 1}})
        self.assertFalse(form_w_hstore.has_changed())

        form_w_hstore = HStoreFormTest({"f1": '{"a": 2}'}, initial={"f1": {"a": 1}})
        self.assertTrue(form_w_hstore.has_changed())
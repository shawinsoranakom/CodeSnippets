def test_render_required_attributes(self):
        form = PartiallyRequiredForm({"f_0": "Hello", "f_1": ""})
        self.assertTrue(form.is_valid())
        self.assertInHTML(
            '<input type="text" name="f_0" value="Hello" required id="id_f_0">',
            form.as_p(),
        )
        self.assertInHTML('<input type="text" name="f_1" id="id_f_1">', form.as_p())
        form = PartiallyRequiredForm({"f_0": "", "f_1": ""})
        self.assertFalse(form.is_valid())
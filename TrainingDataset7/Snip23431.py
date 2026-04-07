def test_attr_false_not_rendered(self):
        html = '<input type="None" name="name" value="value">'
        self.check_html(Input(), "name", "value", html=html, attrs={"readonly": False})
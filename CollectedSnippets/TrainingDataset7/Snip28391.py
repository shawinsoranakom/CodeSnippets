def test_auto_id(self):
        f = BaseCategoryForm(auto_id=False)
        self.assertHTMLEqual(
            str(f.as_ul()),
            """<li>Name: <input type="text" name="name" maxlength="20" required></li>
<li>Slug: <input type="text" name="slug" maxlength="20" required></li>
<li>The URL: <input type="text" name="url" maxlength="40" required></li>""",
        )
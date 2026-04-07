def test_base_form(self):
        self.assertEqual(Category.objects.count(), 0)
        f = BaseCategoryForm()
        self.assertHTMLEqual(
            str(f),
            '<div><label for="id_name">Name:</label><input type="text" name="name" '
            'maxlength="20" required id="id_name"></div><div><label for="id_slug">Slug:'
            '</label><input type="text" name="slug" maxlength="20" required '
            'id="id_slug"></div><div><label for="id_url">The URL:</label>'
            '<input type="text" name="url" maxlength="40" required id="id_url"></div>',
        )
        self.assertHTMLEqual(
            str(f.as_ul()),
            """
            <li><label for="id_name">Name:</label>
            <input id="id_name" type="text" name="name" maxlength="20" required></li>
            <li><label for="id_slug">Slug:</label>
            <input id="id_slug" type="text" name="slug" maxlength="20" required></li>
            <li><label for="id_url">The URL:</label>
            <input id="id_url" type="text" name="url" maxlength="40" required></li>
            """,
        )
        self.assertHTMLEqual(
            str(f["name"]),
            """<input id="id_name" type="text" name="name" maxlength="20" required>""",
        )
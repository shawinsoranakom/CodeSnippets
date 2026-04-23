def test_label_suffix(self):
        # You can specify the 'label_suffix' argument to a Form class to modify
        # the punctuation symbol used at the end of a label. By default, the
        # colon (:) is used, and is only appended to the label if the label
        # doesn't already end with a punctuation symbol: ., !, ? or :. If you
        # specify a different suffix, it will be appended regardless of the
        # last character of the label.
        class FavoriteForm(Form):
            color = CharField(label="Favorite color?")
            animal = CharField(label="Favorite animal")
            answer = CharField(label="Secret answer", label_suffix=" =")

        f = FavoriteForm(auto_id=False)
        self.assertHTMLEqual(
            f.as_ul(),
            """<li>Favorite color? <input type="text" name="color" required></li>
<li>Favorite animal: <input type="text" name="animal" required></li>
<li>Secret answer = <input type="text" name="answer" required></li>""",
        )

        f = FavoriteForm(auto_id=False, label_suffix="?")
        self.assertHTMLEqual(
            f.as_ul(),
            """<li>Favorite color? <input type="text" name="color" required></li>
<li>Favorite animal? <input type="text" name="animal" required></li>
<li>Secret answer = <input type="text" name="answer" required></li>""",
        )

        f = FavoriteForm(auto_id=False, label_suffix="")
        self.assertHTMLEqual(
            f.as_ul(),
            """<li>Favorite color? <input type="text" name="color" required></li>
<li>Favorite animal <input type="text" name="animal" required></li>
<li>Secret answer = <input type="text" name="answer" required></li>""",
        )

        f = FavoriteForm(auto_id=False, label_suffix="\u2192")
        self.assertHTMLEqual(
            f.as_ul(),
            '<li>Favorite color? <input type="text" name="color" required></li>\n'
            "<li>Favorite animal\u2192 "
            '<input type="text" name="animal" required></li>\n'
            '<li>Secret answer = <input type="text" name="answer" required></li>',
        )
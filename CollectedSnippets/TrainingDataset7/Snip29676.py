def test_rendering(self):
        class SplitForm(forms.Form):
            array = SplitArrayField(forms.CharField(), size=3)

        self.assertHTMLEqual(
            str(SplitForm()),
            """
            <div>
                <label for="id_array_0">Array:</label>
                <input id="id_array_0" name="array_0" type="text" required>
                <input id="id_array_1" name="array_1" type="text" required>
                <input id="id_array_2" name="array_2" type="text" required>
            </div>
        """,
        )
def test_rendering(self):
        class RangeForm(forms.Form):
            ints = pg_forms.IntegerRangeField()

        self.assertHTMLEqual(
            str(RangeForm()),
            """
        <div>
            <fieldset>
                <legend>Ints:</legend>
                <input id="id_ints_0" name="ints_0" type="number">
                <input id="id_ints_1" name="ints_1" type="number">
            </fieldset>
        </div>
        """,
        )
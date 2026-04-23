def test_form_as_table_data(self):
        form = ComplexFieldForm(
            {
                "field1_0": "some text",
                "field1_1": ["J", "P"],
                "field1_2_0": "2007-04-25",
                "field1_2_1": "06:24:00",
            }
        )
        self.assertHTMLEqual(
            form.as_table(),
            """
            <tr><th><label>Field1:</label></th>
            <td><input type="text" name="field1_0" value="some text" id="id_field1_0"
                required>
            <select multiple name="field1_1" id="id_field1_1" required>
            <option value="J" selected>John</option>
            <option value="P" selected>Paul</option>
            <option value="G">George</option>
            <option value="R">Ringo</option>
            </select>
            <input type="text" name="field1_2_0" value="2007-04-25" id="id_field1_2_0"
                required>
            <input type="text" name="field1_2_1" value="06:24:00" id="id_field1_2_1"
                required></td></tr>
            """,
        )
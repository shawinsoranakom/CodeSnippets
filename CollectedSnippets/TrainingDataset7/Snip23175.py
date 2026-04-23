def test_callable_initial_value(self):
        """
        The initial value for a callable default returning a queryset is the
        pk.
        """
        ChoiceOptionModel.objects.create(id=1, name="default")
        ChoiceOptionModel.objects.create(id=2, name="option 2")
        ChoiceOptionModel.objects.create(id=3, name="option 3")
        self.assertHTMLEqual(
            ChoiceFieldForm().as_p(),
            """
            <p><label for="id_choice">Choice:</label>
            <select name="choice" id="id_choice">
            <option value="1" selected>ChoiceOption 1</option>
            <option value="2">ChoiceOption 2</option>
            <option value="3">ChoiceOption 3</option>
            </select>
            <input type="hidden" name="initial-choice" value="1" id="initial-id_choice">
            </p>
            <p><label for="id_choice_int">Choice int:</label>
            <select name="choice_int" id="id_choice_int">
            <option value="1" selected>ChoiceOption 1</option>
            <option value="2">ChoiceOption 2</option>
            <option value="3">ChoiceOption 3</option>
            </select>
            <input type="hidden" name="initial-choice_int" value="1"
                id="initial-id_choice_int">
            </p>
            <p><label for="id_multi_choice">Multi choice:</label>
            <select multiple name="multi_choice" id="id_multi_choice" required>
            <option value="1" selected>ChoiceOption 1</option>
            <option value="2">ChoiceOption 2</option>
            <option value="3">ChoiceOption 3</option>
            </select>
            <input type="hidden" name="initial-multi_choice" value="1"
                id="initial-id_multi_choice_0">
            </p>
            <p><label for="id_multi_choice_int">Multi choice int:</label>
            <select multiple name="multi_choice_int" id="id_multi_choice_int" required>
            <option value="1" selected>ChoiceOption 1</option>
            <option value="2">ChoiceOption 2</option>
            <option value="3">ChoiceOption 3</option>
            </select>
            <input type="hidden" name="initial-multi_choice_int" value="1"
                id="initial-id_multi_choice_int_0">
            </p>
            """,
        )
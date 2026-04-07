def test_initial_instance_value(self):
        "Initial instances for model fields may also be instances (refs #7287)"
        ChoiceOptionModel.objects.create(id=1, name="default")
        obj2 = ChoiceOptionModel.objects.create(id=2, name="option 2")
        obj3 = ChoiceOptionModel.objects.create(id=3, name="option 3")
        self.assertHTMLEqual(
            ChoiceFieldForm(
                initial={
                    "choice": obj2,
                    "choice_int": obj2,
                    "multi_choice": [obj2, obj3],
                    "multi_choice_int": ChoiceOptionModel.objects.exclude(
                        name="default"
                    ),
                }
            ).as_p(),
            """
            <p><label for="id_choice">Choice:</label>
            <select name="choice" id="id_choice">
            <option value="1">ChoiceOption 1</option>
            <option value="2" selected>ChoiceOption 2</option>
            <option value="3">ChoiceOption 3</option>
            </select>
            <input type="hidden" name="initial-choice" value="2" id="initial-id_choice">
            </p>
            <p><label for="id_choice_int">Choice int:</label>
            <select name="choice_int" id="id_choice_int">
            <option value="1">ChoiceOption 1</option>
            <option value="2" selected>ChoiceOption 2</option>
            <option value="3">ChoiceOption 3</option>
            </select>
            <input type="hidden" name="initial-choice_int" value="2"
                id="initial-id_choice_int">
            </p>
            <p><label for="id_multi_choice">Multi choice:</label>
            <select multiple name="multi_choice" id="id_multi_choice" required>
            <option value="1">ChoiceOption 1</option>
            <option value="2" selected>ChoiceOption 2</option>
            <option value="3" selected>ChoiceOption 3</option>
            </select>
            <input type="hidden" name="initial-multi_choice" value="2"
                id="initial-id_multi_choice_0">
            <input type="hidden" name="initial-multi_choice" value="3"
                id="initial-id_multi_choice_1">
            </p>
            <p><label for="id_multi_choice_int">Multi choice int:</label>
            <select multiple name="multi_choice_int" id="id_multi_choice_int" required>
            <option value="1">ChoiceOption 1</option>
            <option value="2" selected>ChoiceOption 2</option>
            <option value="3" selected>ChoiceOption 3</option>
            </select>
            <input type="hidden" name="initial-multi_choice_int" value="2"
                id="initial-id_multi_choice_int_0">
            <input type="hidden" name="initial-multi_choice_int" value="3"
                id="initial-id_multi_choice_int_1">
            </p>
            """,
        )
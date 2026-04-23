def test_model_inheritance(self):
        BetterAuthorFormSet = modelformset_factory(BetterAuthor, fields="__all__")
        formset = BetterAuthorFormSet()
        self.assertEqual(len(formset.forms), 1)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label>'
            '<input id="id_form-0-name" type="text" name="form-0-name" maxlength="100">'
            '</p><p><label for="id_form-0-write_speed">Write speed:</label>'
            '<input type="number" name="form-0-write_speed" id="id_form-0-write_speed">'
            '<input type="hidden" name="form-0-author_ptr" id="id_form-0-author_ptr">'
            "</p>",
        )

        data = {
            "form-TOTAL_FORMS": "1",  # the number of forms rendered
            "form-INITIAL_FORMS": "0",  # the number of forms with initial data
            "form-MAX_NUM_FORMS": "",  # the max number of forms
            "form-0-author_ptr": "",
            "form-0-name": "Ernest Hemingway",
            "form-0-write_speed": "10",
        }

        formset = BetterAuthorFormSet(data)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (author1,) = saved
        self.assertEqual(author1, BetterAuthor.objects.get(name="Ernest Hemingway"))
        hemingway_id = BetterAuthor.objects.get(name="Ernest Hemingway").pk

        formset = BetterAuthorFormSet()
        self.assertEqual(len(formset.forms), 2)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label>'
            '<input id="id_form-0-name" type="text" name="form-0-name" '
            'value="Ernest Hemingway" maxlength="100"></p>'
            '<p><label for="id_form-0-write_speed">Write speed:</label>'
            '<input type="number" name="form-0-write_speed" value="10" '
            'id="id_form-0-write_speed">'
            '<input type="hidden" name="form-0-author_ptr" value="%s" '
            'id="id_form-0-author_ptr"></p>' % hemingway_id,
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_form-1-name">Name:</label>'
            '<input id="id_form-1-name" type="text" name="form-1-name" maxlength="100">'
            '</p><p><label for="id_form-1-write_speed">Write speed:</label>'
            '<input type="number" name="form-1-write_speed" id="id_form-1-write_speed">'
            '<input type="hidden" name="form-1-author_ptr" id="id_form-1-author_ptr">'
            "</p>",
        )

        data = {
            "form-TOTAL_FORMS": "2",  # the number of forms rendered
            "form-INITIAL_FORMS": "1",  # the number of forms with initial data
            "form-MAX_NUM_FORMS": "",  # the max number of forms
            "form-0-author_ptr": hemingway_id,
            "form-0-name": "Ernest Hemingway",
            "form-0-write_speed": "10",
            "form-1-author_ptr": "",
            "form-1-name": "",
            "form-1-write_speed": "",
        }

        formset = BetterAuthorFormSet(data)
        self.assertTrue(formset.is_valid())
        self.assertEqual(formset.save(), [])
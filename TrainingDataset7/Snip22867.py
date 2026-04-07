def test_use_required_attribute_true(self):
        class MyForm(Form):
            use_required_attribute = True
            f1 = CharField(max_length=30)
            f2 = CharField(max_length=30, required=False)
            f3 = CharField(widget=Textarea)
            f4 = ChoiceField(choices=[("P", "Python"), ("J", "Java")])

        form = MyForm()
        self.assertHTMLEqual(
            form.as_p(),
            '<p><label for="id_f1">F1:</label>'
            '<input id="id_f1" maxlength="30" name="f1" type="text" required></p>'
            '<p><label for="id_f2">F2:</label>'
            '<input id="id_f2" maxlength="30" name="f2" type="text"></p>'
            '<p><label for="id_f3">F3:</label>'
            '<textarea cols="40" id="id_f3" name="f3" rows="10" required>'
            "</textarea></p>"
            '<p><label for="id_f4">F4:</label> <select id="id_f4" name="f4">'
            '<option value="P">Python</option>'
            '<option value="J">Java</option>'
            "</select></p>",
        )
        self.assertHTMLEqual(
            form.as_ul(),
            '<li><label for="id_f1">F1:</label> '
            '<input id="id_f1" maxlength="30" name="f1" type="text" required></li>'
            '<li><label for="id_f2">F2:</label>'
            '<input id="id_f2" maxlength="30" name="f2" type="text"></li>'
            '<li><label for="id_f3">F3:</label>'
            '<textarea cols="40" id="id_f3" name="f3" rows="10" required>'
            "</textarea></li>"
            '<li><label for="id_f4">F4:</label> <select id="id_f4" name="f4">'
            '<option value="P">Python</option>'
            '<option value="J">Java</option>'
            "</select></li>",
        )
        self.assertHTMLEqual(
            form.as_table(),
            '<tr><th><label for="id_f1">F1:</label></th>'
            '<td><input id="id_f1" maxlength="30" name="f1" type="text" required>'
            "</td></tr>"
            '<tr><th><label for="id_f2">F2:</label></th>'
            '<td><input id="id_f2" maxlength="30" name="f2" type="text"></td></tr>'
            '<tr><th><label for="id_f3">F3:</label></th>'
            '<td><textarea cols="40" id="id_f3" name="f3" rows="10" required>'
            "</textarea></td></tr>"
            '<tr><th><label for="id_f4">F4:</label></th><td>'
            '<select id="id_f4" name="f4">'
            '<option value="P">Python</option>'
            '<option value="J">Java</option>'
            "</select></td></tr>",
        )
        self.assertHTMLEqual(
            form.render(form.template_name_div),
            '<div><label for="id_f1">F1:</label><input id="id_f1" maxlength="30" '
            'name="f1" type="text" required></div><div><label for="id_f2">F2:</label>'
            '<input id="id_f2" maxlength="30" name="f2" type="text"></div><div><label '
            'for="id_f3">F3:</label><textarea cols="40" id="id_f3" name="f3" '
            'rows="10" required></textarea></div><div><label for="id_f4">F4:</label>'
            '<select id="id_f4" name="f4"><option value="P">Python</option>'
            '<option value="J">Java</option></select></div>',
        )
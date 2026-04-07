def test_callable_defaults(self):
        # Use of callable defaults (see bug #7975).

        person = Person.objects.create(name="Ringo")
        FormSet = inlineformset_factory(
            Person, Membership, can_delete=False, extra=1, fields="__all__"
        )
        formset = FormSet(instance=person)

        # Django will render a hidden field for model fields that have a
        # callable default. This is required to ensure the value is tested for
        # change correctly when determine what extra forms have changed to
        # save.

        self.assertEqual(len(formset.forms), 1)  # this formset only has one form
        form = formset.forms[0]
        now = form.fields["date_joined"].initial()
        result = form.as_p()
        result = re.sub(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?",
            "__DATETIME__",
            result,
        )
        self.assertHTMLEqual(
            result,
            '<p><label for="id_membership_set-0-date_joined">Date joined:</label>'
            '<input type="text" name="membership_set-0-date_joined" '
            'value="__DATETIME__" id="id_membership_set-0-date_joined">'
            '<input type="hidden" name="initial-membership_set-0-date_joined" '
            'value="__DATETIME__" '
            'id="initial-membership_set-0-id_membership_set-0-date_joined"></p>'
            '<p><label for="id_membership_set-0-karma">Karma:</label>'
            '<input type="number" name="membership_set-0-karma" '
            'id="id_membership_set-0-karma">'
            '<input type="hidden" name="membership_set-0-person" value="%s" '
            'id="id_membership_set-0-person">'
            '<input type="hidden" name="membership_set-0-id" '
            'id="id_membership_set-0-id"></p>' % person.id,
        )

        # test for validation with callable defaults. Validations rely on
        # hidden fields

        data = {
            "membership_set-TOTAL_FORMS": "1",
            "membership_set-INITIAL_FORMS": "0",
            "membership_set-MAX_NUM_FORMS": "",
            "membership_set-0-date_joined": now.strftime("%Y-%m-%d %H:%M:%S"),
            "initial-membership_set-0-date_joined": now.strftime("%Y-%m-%d %H:%M:%S"),
            "membership_set-0-karma": "",
        }
        formset = FormSet(data, instance=person)
        self.assertTrue(formset.is_valid())

        # now test for when the data changes

        one_day_later = now + datetime.timedelta(days=1)
        filled_data = {
            "membership_set-TOTAL_FORMS": "1",
            "membership_set-INITIAL_FORMS": "0",
            "membership_set-MAX_NUM_FORMS": "",
            "membership_set-0-date_joined": one_day_later.strftime("%Y-%m-%d %H:%M:%S"),
            "initial-membership_set-0-date_joined": now.strftime("%Y-%m-%d %H:%M:%S"),
            "membership_set-0-karma": "",
        }
        formset = FormSet(filled_data, instance=person)
        self.assertFalse(formset.is_valid())

        # now test with split datetime fields

        class MembershipForm(forms.ModelForm):
            date_joined = forms.SplitDateTimeField(initial=now)

            class Meta:
                model = Membership
                fields = "__all__"

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.fields["date_joined"].widget = forms.SplitDateTimeWidget()

        FormSet = inlineformset_factory(
            Person,
            Membership,
            form=MembershipForm,
            can_delete=False,
            extra=1,
            fields="__all__",
        )
        data = {
            "membership_set-TOTAL_FORMS": "1",
            "membership_set-INITIAL_FORMS": "0",
            "membership_set-MAX_NUM_FORMS": "",
            "membership_set-0-date_joined_0": now.strftime("%Y-%m-%d"),
            "membership_set-0-date_joined_1": now.strftime("%H:%M:%S"),
            "initial-membership_set-0-date_joined": now.strftime("%Y-%m-%d %H:%M:%S"),
            "membership_set-0-karma": "",
        }
        formset = FormSet(data, instance=person)
        self.assertTrue(formset.is_valid())
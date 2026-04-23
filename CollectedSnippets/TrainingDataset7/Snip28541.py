def test_custom_pk(self):
        # We need to ensure that it is displayed

        CustomPrimaryKeyFormSet = modelformset_factory(
            CustomPrimaryKey, fields="__all__"
        )
        formset = CustomPrimaryKeyFormSet()
        self.assertEqual(len(formset.forms), 1)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_form-0-my_pk">My pk:</label>'
            '<input id="id_form-0-my_pk" type="text" name="form-0-my_pk" '
            'maxlength="10"></p>'
            '<p><label for="id_form-0-some_field">Some field:</label>'
            '<input id="id_form-0-some_field" type="text" name="form-0-some_field" '
            'maxlength="100"></p>',
        )

        # Custom primary keys with ForeignKey, OneToOneField and AutoField.

        place = Place.objects.create(pk=1, name="Giordanos", city="Chicago")

        FormSet = inlineformset_factory(
            Place, Owner, extra=2, can_delete=False, fields="__all__"
        )
        formset = FormSet(instance=place)
        self.assertEqual(len(formset.forms), 2)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_owner_set-0-name">Name:</label>'
            '<input id="id_owner_set-0-name" type="text" name="owner_set-0-name" '
            'maxlength="100">'
            '<input type="hidden" name="owner_set-0-place" value="1" '
            'id="id_owner_set-0-place">'
            '<input type="hidden" name="owner_set-0-auto_id" '
            'id="id_owner_set-0-auto_id"></p>',
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_owner_set-1-name">Name:</label>'
            '<input id="id_owner_set-1-name" type="text" name="owner_set-1-name" '
            'maxlength="100">'
            '<input type="hidden" name="owner_set-1-place" value="1" '
            'id="id_owner_set-1-place">'
            '<input type="hidden" name="owner_set-1-auto_id" '
            'id="id_owner_set-1-auto_id"></p>',
        )

        data = {
            "owner_set-TOTAL_FORMS": "2",
            "owner_set-INITIAL_FORMS": "0",
            "owner_set-MAX_NUM_FORMS": "",
            "owner_set-0-auto_id": "",
            "owner_set-0-name": "Joe Perry",
            "owner_set-1-auto_id": "",
            "owner_set-1-name": "",
        }
        formset = FormSet(data, instance=place)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (owner1,) = saved
        self.assertEqual(owner1.name, "Joe Perry")
        self.assertEqual(owner1.place.name, "Giordanos")

        formset = FormSet(instance=place)
        self.assertEqual(len(formset.forms), 3)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_owner_set-0-name">Name:</label>'
            '<input id="id_owner_set-0-name" type="text" name="owner_set-0-name" '
            'value="Joe Perry" maxlength="100">'
            '<input type="hidden" name="owner_set-0-place" value="1" '
            'id="id_owner_set-0-place">'
            '<input type="hidden" name="owner_set-0-auto_id" value="%s" '
            'id="id_owner_set-0-auto_id"></p>' % owner1.auto_id,
        )
        self.assertHTMLEqual(
            formset.forms[1].as_p(),
            '<p><label for="id_owner_set-1-name">Name:</label>'
            '<input id="id_owner_set-1-name" type="text" name="owner_set-1-name" '
            'maxlength="100">'
            '<input type="hidden" name="owner_set-1-place" value="1" '
            'id="id_owner_set-1-place">'
            '<input type="hidden" name="owner_set-1-auto_id" '
            'id="id_owner_set-1-auto_id"></p>',
        )
        self.assertHTMLEqual(
            formset.forms[2].as_p(),
            '<p><label for="id_owner_set-2-name">Name:</label>'
            '<input id="id_owner_set-2-name" type="text" name="owner_set-2-name" '
            'maxlength="100">'
            '<input type="hidden" name="owner_set-2-place" value="1" '
            'id="id_owner_set-2-place">'
            '<input type="hidden" name="owner_set-2-auto_id" '
            'id="id_owner_set-2-auto_id"></p>',
        )

        data = {
            "owner_set-TOTAL_FORMS": "3",
            "owner_set-INITIAL_FORMS": "1",
            "owner_set-MAX_NUM_FORMS": "",
            "owner_set-0-auto_id": str(owner1.auto_id),
            "owner_set-0-name": "Joe Perry",
            "owner_set-1-auto_id": "",
            "owner_set-1-name": "Jack Berry",
            "owner_set-2-auto_id": "",
            "owner_set-2-name": "",
        }
        formset = FormSet(data, instance=place)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (owner2,) = saved
        self.assertEqual(owner2.name, "Jack Berry")
        self.assertEqual(owner2.place.name, "Giordanos")

        # A custom primary key that is a ForeignKey or OneToOneField get
        # rendered for the user to choose.
        FormSet = modelformset_factory(OwnerProfile, fields="__all__")
        formset = FormSet()
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_form-0-owner">Owner:</label>'
            '<select name="form-0-owner" id="id_form-0-owner">'
            '<option value="" selected>---------</option>'
            '<option value="%s">Joe Perry at Giordanos</option>'
            '<option value="%s">Jack Berry at Giordanos</option>'
            "</select></p>"
            '<p><label for="id_form-0-age">Age:</label>'
            '<input type="number" name="form-0-age" id="id_form-0-age" min="0"></p>'
            % (owner1.auto_id, owner2.auto_id),
        )

        owner1 = Owner.objects.get(name="Joe Perry")
        FormSet = inlineformset_factory(
            Owner, OwnerProfile, max_num=1, can_delete=False, fields="__all__"
        )
        self.assertEqual(FormSet.max_num, 1)

        formset = FormSet(instance=owner1)
        self.assertEqual(len(formset.forms), 1)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_ownerprofile-0-age">Age:</label>'
            '<input type="number" name="ownerprofile-0-age" '
            'id="id_ownerprofile-0-age" min="0">'
            '<input type="hidden" name="ownerprofile-0-owner" value="%s" '
            'id="id_ownerprofile-0-owner"></p>' % owner1.auto_id,
        )

        data = {
            "ownerprofile-TOTAL_FORMS": "1",
            "ownerprofile-INITIAL_FORMS": "0",
            "ownerprofile-MAX_NUM_FORMS": "1",
            "ownerprofile-0-owner": "",
            "ownerprofile-0-age": "54",
        }
        formset = FormSet(data, instance=owner1)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (profile1,) = saved
        self.assertEqual(profile1.owner, owner1)
        self.assertEqual(profile1.age, 54)

        formset = FormSet(instance=owner1)
        self.assertEqual(len(formset.forms), 1)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_ownerprofile-0-age">Age:</label>'
            '<input type="number" name="ownerprofile-0-age" value="54" '
            'id="id_ownerprofile-0-age" min="0">'
            '<input type="hidden" name="ownerprofile-0-owner" value="%s" '
            'id="id_ownerprofile-0-owner"></p>' % owner1.auto_id,
        )

        data = {
            "ownerprofile-TOTAL_FORMS": "1",
            "ownerprofile-INITIAL_FORMS": "1",
            "ownerprofile-MAX_NUM_FORMS": "1",
            "ownerprofile-0-owner": str(owner1.auto_id),
            "ownerprofile-0-age": "55",
        }
        formset = FormSet(data, instance=owner1)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (profile1,) = saved
        self.assertEqual(profile1.owner, owner1)
        self.assertEqual(profile1.age, 55)
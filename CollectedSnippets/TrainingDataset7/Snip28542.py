def test_unique_true_enforces_max_num_one(self):
        # ForeignKey with unique=True should enforce max_num=1

        place = Place.objects.create(pk=1, name="Giordanos", city="Chicago")

        FormSet = inlineformset_factory(
            Place, Location, can_delete=False, fields="__all__"
        )
        self.assertEqual(FormSet.max_num, 1)

        formset = FormSet(instance=place)
        self.assertEqual(len(formset.forms), 1)
        self.assertHTMLEqual(
            formset.forms[0].as_p(),
            '<p><label for="id_location_set-0-lat">Lat:</label>'
            '<input id="id_location_set-0-lat" type="text" name="location_set-0-lat" '
            'maxlength="100"></p>'
            '<p><label for="id_location_set-0-lon">Lon:</label>'
            '<input id="id_location_set-0-lon" type="text" name="location_set-0-lon" '
            'maxlength="100">'
            '<input type="hidden" name="location_set-0-place" value="1" '
            'id="id_location_set-0-place">'
            '<input type="hidden" name="location_set-0-id" '
            'id="id_location_set-0-id"></p>',
        )
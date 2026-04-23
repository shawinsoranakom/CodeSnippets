def _test_choices(request, expected_displays):
            request.user = self.alfred
            changelist = modeladmin.get_changelist_instance(request)
            filterspec = changelist.get_filters(request)[0][0]
            self.assertEqual(filterspec.title, "publication decade")
            choices = tuple(c["display"] for c in filterspec.choices(changelist))
            self.assertEqual(choices, expected_displays)
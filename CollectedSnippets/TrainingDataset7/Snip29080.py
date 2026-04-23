def test_default_foreign_key_widget(self):
        # First, without any radio_fields specified, the widgets for ForeignKey
        # and fields with choices specified ought to be a basic Select widget.
        # ForeignKey widgets in the admin are wrapped with
        # RelatedFieldWidgetWrapper so they need to be handled properly when
        # type checking. For Select fields, all of the choices lists have a
        # first entry of dashes.
        cma = ModelAdmin(Concert, self.site)
        cmafa = cma.get_form(request)

        self.assertEqual(type(cmafa.base_fields["main_band"].widget.widget), Select)
        self.assertEqual(
            list(cmafa.base_fields["main_band"].widget.choices),
            [("", "---------"), (self.band.id, "The Doors")],
        )

        self.assertEqual(type(cmafa.base_fields["opening_band"].widget.widget), Select)
        self.assertEqual(
            list(cmafa.base_fields["opening_band"].widget.choices),
            [("", "---------"), (self.band.id, "The Doors")],
        )
        self.assertEqual(type(cmafa.base_fields["day"].widget), Select)
        self.assertEqual(
            list(cmafa.base_fields["day"].widget.choices),
            [("", "---------"), (1, "Fri"), (2, "Sat")],
        )
        self.assertEqual(type(cmafa.base_fields["transport"].widget), Select)
        self.assertEqual(
            list(cmafa.base_fields["transport"].widget.choices),
            [("", "---------"), (1, "Plane"), (2, "Train"), (3, "Bus")],
        )
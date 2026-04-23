def test_widget_has_changed(self):
        geoadmin = self.admin_site.get_model_admin(City)
        form = geoadmin.get_changelist_form(None)()
        has_changed = form.fields["point"].has_changed

        initial = Point(13.4197458572965953, 52.5194108501149799, srid=4326)
        data_same = "SRID=3857;POINT(1493879.2754093995 6894592.019687599)"
        data_almost_same = "SRID=3857;POINT(1493879.2754093990 6894592.019687590)"
        data_changed = "SRID=3857;POINT(1493884.0527237 6894593.8111804)"

        self.assertIs(has_changed(None, data_changed), True)
        self.assertIs(has_changed(initial, ""), True)
        self.assertIs(has_changed(None, ""), False)
        self.assertIs(has_changed(initial, data_same), False)
        self.assertIs(has_changed(initial, data_almost_same), False)
        self.assertIs(has_changed(initial, data_changed), True)
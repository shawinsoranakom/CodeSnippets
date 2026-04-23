def test_fk_related_model_not_in_admin(self):
        # FK to a model not registered with admin site. Raw ID widget should
        # have no magnifying glass link. See #16542
        big_honeycomb = Honeycomb.objects.create(location="Old tree")
        big_honeycomb.bee_set.create()
        rel = Bee._meta.get_field("honeycomb").remote_field

        w = widgets.ForeignKeyRawIdWidget(rel, widget_admin_site)
        self.assertHTMLEqual(
            w.render("honeycomb_widget", big_honeycomb.pk, attrs={}),
            '<input type="text" name="honeycomb_widget" value="%(hcombpk)s">'
            "&nbsp;<strong>%(hcomb)s</strong>"
            % {"hcombpk": big_honeycomb.pk, "hcomb": big_honeycomb},
        )
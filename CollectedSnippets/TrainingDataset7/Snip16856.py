def test_fk_to_self_model_not_in_admin(self):
        # FK to self, not registered with admin site. Raw ID widget should have
        # no magnifying glass link. See #16542
        subject1 = Individual.objects.create(name="Subject #1")
        Individual.objects.create(name="Child", parent=subject1)
        rel = Individual._meta.get_field("parent").remote_field

        w = widgets.ForeignKeyRawIdWidget(rel, widget_admin_site)
        self.assertHTMLEqual(
            w.render("individual_widget", subject1.pk, attrs={}),
            '<input type="text" name="individual_widget" value="%(subj1pk)s">'
            "&nbsp;<strong>%(subj1)s</strong>"
            % {"subj1pk": subject1.pk, "subj1": subject1},
        )
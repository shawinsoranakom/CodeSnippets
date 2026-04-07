def test_m2m_related_model_not_in_admin(self):
        # M2M relationship with model not registered with admin site. Raw ID
        # widget should have no magnifying glass link. See #16542
        consultor1 = Advisor.objects.create(name="Rockstar Techie")

        c1 = Company.objects.create(name="Doodle")
        c2 = Company.objects.create(name="Pear")
        consultor1.companies.add(c1, c2)
        rel = Advisor._meta.get_field("companies").remote_field

        w = widgets.ManyToManyRawIdWidget(rel, widget_admin_site)
        self.assertHTMLEqual(
            w.render("company_widget1", [c1.pk, c2.pk], attrs={}),
            '<input type="text" name="company_widget1" value="%(c1pk)s,%(c2pk)s">'
            % {"c1pk": c1.pk, "c2pk": c2.pk},
        )

        self.assertHTMLEqual(
            w.render("company_widget2", [c1.pk]),
            '<input type="text" name="company_widget2" value="%(c1pk)s">'
            % {"c1pk": c1.pk},
        )
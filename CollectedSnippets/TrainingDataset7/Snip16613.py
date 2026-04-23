def test_readonly_onetoone_backwards_ref(self):
        """
        Can reference a reverse OneToOneField in ModelAdmin.readonly_fields.
        """
        v1 = Villain.objects.create(name="Adam")
        pl = Plot.objects.create(name="Test Plot", team_leader=v1, contact=v1)
        pd = PlotDetails.objects.create(details="Brand New Plot", plot=pl)

        response = self.client.get(
            reverse("admin:admin_views_plotproxy_change", args=(pl.pk,))
        )
        field = self.get_admin_readonly_field(response, "plotdetails")
        pd_url = reverse("admin:admin_views_plotdetails_change", args=(pd.pk,))
        self.assertEqual(field.contents(), '<a href="%s">Brand New Plot</a>' % pd_url)

        # The reverse relation also works if the OneToOneField is null.
        pd.plot = None
        pd.save()

        response = self.client.get(
            reverse("admin:admin_views_plotproxy_change", args=(pl.pk,))
        )
        field = self.get_admin_readonly_field(response, "plotdetails")
        self.assertEqual(field.contents(), "-")
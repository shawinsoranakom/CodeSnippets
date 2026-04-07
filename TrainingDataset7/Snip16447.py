def test_nesting(self):
        """
        Objects should be nested to display the relationships that
        cause them to be scheduled for deletion.
        """
        pattern = re.compile(
            r'<li>Plot: <a href="%s">World Domination</a>\s*<ul>\s*'
            r'<li>Plot details: <a href="%s">almost finished</a>'
            % (
                reverse("admin:admin_views_plot_change", args=(self.pl1.pk,)),
                reverse("admin:admin_views_plotdetails_change", args=(self.pd1.pk,)),
            )
        )
        response = self.client.get(
            reverse("admin:admin_views_villain_delete", args=(self.v1.pk,))
        )
        self.assertRegex(response.text, pattern)
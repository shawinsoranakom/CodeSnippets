def test_named_group_field_choices_filter(self):
        """
        Ensures the filter UI shows correctly when at least one named group has
        been used in the choices option of a model field.
        """
        response = self.client.get(reverse("admin:admin_views_fabric_changelist"))
        fail_msg = (
            "Changelist filter isn't showing options contained inside a model "
            "field 'choices' option named group."
        )
        self.assertContains(
            response,
            '<search id="changelist-filter" '
            'aria-labelledby="changelist-filter-header">',
        )
        self.assertContains(
            response,
            '<a href="?surface__exact=x">Horizontal</a>',
            msg_prefix=fail_msg,
            html=True,
        )
        self.assertContains(
            response,
            '<a href="?surface__exact=y">Vertical</a>',
            msg_prefix=fail_msg,
            html=True,
        )
def test_named_group_field_choices_change_list(self):
        """
        Ensures the admin changelist shows correct values in the relevant
        column for rows corresponding to instances of a model in which a named
        group has been used in the choices option of a field.
        """
        link1 = reverse("admin:admin_views_fabric_change", args=(self.fab1.pk,))
        link2 = reverse("admin:admin_views_fabric_change", args=(self.fab2.pk,))
        response = self.client.get(reverse("admin:admin_views_fabric_changelist"))
        fail_msg = (
            "Changelist table isn't showing the right human-readable values "
            "set by a model field 'choices' option named group."
        )
        self.assertContains(
            response,
            '<a href="%s">Horizontal</a>' % link1,
            msg_prefix=fail_msg,
            html=True,
        )
        self.assertContains(
            response,
            '<a href="%s">Vertical</a>' % link2,
            msg_prefix=fail_msg,
            html=True,
        )
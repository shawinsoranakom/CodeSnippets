def test_result_list_html(self):
        """
        Inclusion tag result_list generates a table when with default
        ModelAdmin settings.
        """
        new_parent = Parent.objects.create(name="parent")
        new_child = Child.objects.create(name="name", parent=new_parent)
        request = self.factory.get("/child/")
        request.user = self.superuser
        m = ChildAdmin(Child, custom_site)
        cl = m.get_changelist_instance(request)
        template = Template(
            "{% load admin_list %}{% spaceless %}{% result_list cl %}{% endspaceless %}"
        )
        context = Context({"cl": cl, "opts": Child._meta})
        table_output = template.render(context)
        link = reverse("admin:admin_changelist_child_change", args=(new_child.id,))
        row_html = build_tbody_html(
            new_child,
            link,
            "name",
            '<td class="field-parent nowrap">%s</td>' % new_parent,
        )
        self.assertNotEqual(
            table_output.find(row_html),
            -1,
            "Failed to find expected row element: %s" % table_output,
        )
        self.assertInHTML(
            '<input type="checkbox" id="action-toggle" '
            'aria-label="Select all objects on this page for an action">',
            table_output,
        )
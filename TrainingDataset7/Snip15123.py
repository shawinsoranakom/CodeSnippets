def test_result_list_set_empty_value_display_on_admin_site(self):
        """
        Empty value display can be set on AdminSite.
        """
        new_child = Child.objects.create(name="name", parent=None)
        request = self.factory.get("/child/")
        request.user = self.superuser
        # Set a new empty display value on AdminSite.
        admin.site.empty_value_display = "???"
        m = ChildAdmin(Child, admin.site)
        cl = m.get_changelist_instance(request)
        template = Template(
            "{% load admin_list %}{% spaceless %}{% result_list cl %}{% endspaceless %}"
        )
        context = Context({"cl": cl, "opts": Child._meta})
        table_output = template.render(context)
        link = reverse("admin:admin_changelist_child_change", args=(new_child.id,))
        row_html = build_tbody_html(
            new_child, link, "name", '<td class="field-parent nowrap">???</td>'
        )
        self.assertNotEqual(
            table_output.find(row_html),
            -1,
            "Failed to find expected row element: %s" % table_output,
        )
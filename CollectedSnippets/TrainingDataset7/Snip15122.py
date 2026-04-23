def test_result_list_empty_changelist_value_blank_string(self):
        new_child = Child.objects.create(name="", parent=None)
        request = self.factory.get("/child/")
        request.user = self.superuser
        m = ChildAdmin(Child, custom_site)
        cl = m.get_changelist_instance(request)
        cl.formset = None
        template = Template(
            "{% load admin_list %}{% spaceless %}{% result_list cl %}{% endspaceless %}"
        )
        context = Context({"cl": cl, "opts": Child._meta})
        table_output = template.render(context)
        link = reverse("admin:admin_changelist_child_change", args=(new_child.id,))
        row_html = build_tbody_html(
            new_child, link, "-", '<td class="field-parent nowrap">-</td>'
        )
        self.assertInHTML(row_html, table_output)
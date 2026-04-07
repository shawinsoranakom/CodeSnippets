def test_action_checkbox_for_model_with_dunder_html(self):
        grandchild = GrandChild.objects.create(name="name")
        request = self._mocked_authenticated_request("/grandchild/", self.superuser)
        m = GrandChildAdmin(GrandChild, custom_site)
        cl = m.get_changelist_instance(request)
        template = Template(
            "{% load admin_list %}{% spaceless %}{% result_list cl %}{% endspaceless %}"
        )
        context = Context({"cl": cl, "opts": GrandChild._meta})
        table_output = template.render(context)
        link = reverse(
            "admin:admin_changelist_grandchild_change", args=(grandchild.id,)
        )
        row_html = build_tbody_html(
            grandchild,
            link,
            "name",
            '<td class="field-parent__name">-</td>'
            '<td class="field-parent__parent__name">-</td>',
        )
        self.assertNotEqual(
            table_output.find(row_html),
            -1,
            "Failed to find expected row element: %s" % table_output,
        )
def test_result_list_editable_html(self):
        """
        Regression tests for #11791: Inclusion tag result_list generates a
        table and this checks that the items are nested within the table
        element tags.
        Also a regression test for #13599, verifies that hidden fields
        when list_editable is enabled are rendered in a div outside the
        table.
        """
        new_parent = Parent.objects.create(name="parent")
        new_child = Child.objects.create(name="name", parent=new_parent)
        request = self.factory.get("/child/")
        request.user = self.superuser
        m = ChildAdmin(Child, custom_site)

        # Test with list_editable fields
        m.list_display = ["id", "name", "parent"]
        m.list_display_links = ["id"]
        m.list_editable = ["name"]
        cl = m.get_changelist_instance(request)
        FormSet = m.get_changelist_formset(request)
        cl.formset = FormSet(queryset=cl.result_list)
        template = Template(
            "{% load admin_list %}{% spaceless %}{% result_list cl %}{% endspaceless %}"
        )
        context = Context({"cl": cl, "opts": Child._meta})
        table_output = template.render(context)
        # make sure that hidden fields are in the correct place
        hiddenfields_div = (
            '<div class="hiddenfields">'
            '<input type="hidden" name="form-0-id" value="%s" id="id_form-0-id">'
            "</div>"
        ) % new_child.id
        self.assertInHTML(
            hiddenfields_div, table_output, msg_prefix="Failed to find hidden fields"
        )

        # make sure that list editable fields are rendered in divs correctly
        editable_name_field = (
            '<input name="form-0-name" value="name" class="vTextField" '
            'maxlength="30" type="text" id="id_form-0-name">'
        )
        self.assertInHTML(
            '<td class="field-name">%s</td>' % editable_name_field,
            table_output,
            msg_prefix='Failed to find "name" list_editable field',
        )
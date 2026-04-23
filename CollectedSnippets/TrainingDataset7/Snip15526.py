def test_inlines_show_change_link_unregistered(self):
        "Inlines `show_change_link` disabled for unregistered models."
        parent = ParentModelWithCustomPk.objects.create(my_own_pk="foo", name="Foo")
        ChildModel1.objects.create(my_own_pk="bar", name="Bar", parent=parent)
        ChildModel2.objects.create(my_own_pk="baz", name="Baz", parent=parent)
        response = self.client.get(
            reverse("admin:admin_inlines_parentmodelwithcustompk_change", args=("foo",))
        )
        self.assertFalse(
            response.context["inline_admin_formset"].opts.has_registered_model
        )
        self.assertNotContains(response, INLINE_CHANGELINK_HTML)
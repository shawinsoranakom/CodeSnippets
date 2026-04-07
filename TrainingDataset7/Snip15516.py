def test_custom_pk_shortcut(self):
        """
        The "View on Site" link is correct for models with a custom primary key
        field.
        """
        parent = ParentModelWithCustomPk.objects.create(my_own_pk="foo", name="Foo")
        child1 = ChildModel1.objects.create(my_own_pk="bar", name="Bar", parent=parent)
        child2 = ChildModel2.objects.create(my_own_pk="baz", name="Baz", parent=parent)
        response = self.client.get(
            reverse("admin:admin_inlines_parentmodelwithcustompk_change", args=("foo",))
        )
        child1_shortcut = "r/%s/%s/" % (
            ContentType.objects.get_for_model(child1).pk,
            child1.pk,
        )
        child2_shortcut = "r/%s/%s/" % (
            ContentType.objects.get_for_model(child2).pk,
            child2.pk,
        )
        self.assertContains(response, child1_shortcut)
        self.assertContains(response, child2_shortcut)
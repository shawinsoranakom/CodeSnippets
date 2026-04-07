def test_sort_indicators_admin_order(self):
        """
        The admin shows default sort indicators for all kinds of 'ordering'
        fields: field names, method on the model admin and model itself, and
        other callables. See #17252.
        """
        models = [
            (AdminOrderedField, "adminorderedfield"),
            (AdminOrderedModelMethod, "adminorderedmodelmethod"),
            (AdminOrderedAdminMethod, "adminorderedadminmethod"),
            (AdminOrderedCallable, "adminorderedcallable"),
        ]
        for model, url in models:
            model.objects.create(stuff="The Last Item", order=3)
            model.objects.create(stuff="The First Item", order=1)
            model.objects.create(stuff="The Middle Item", order=2)
            response = self.client.get(
                reverse("admin:admin_views_%s_changelist" % url), {}
            )
            # Should have 3 columns including action checkbox col.
            result_list_table_re = re.compile('<table id="result_list">(.*?)</thead>')
            result_list_table_head = result_list_table_re.search(str(response.content))[
                0
            ]
            self.assertEqual(result_list_table_head.count('<th scope="col"'), 3)
            # Check if the correct column was selected. 2 is the index of the
            # 'order' column in the model admin's 'list_display' with 0 being
            # the implicit 'action_checkbox' and 1 being the column 'stuff'.
            self.assertEqual(
                response.context["cl"].get_ordering_field_columns(), {2: "asc"}
            )
            # Check order of records.
            self.assertContentBefore(response, "The First Item", "The Middle Item")
            self.assertContentBefore(response, "The Middle Item", "The Last Item")
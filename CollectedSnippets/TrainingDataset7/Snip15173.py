def test_deterministic_order_for_model_ordered_by_its_manager(self):
        """
        The primary key is used in the ordering of the changelist's results to
        guarantee a deterministic order, even when the model has a manager that
        defines a default ordering (#17198).
        """
        superuser = self._create_superuser("superuser")

        for counter in range(1, 51):
            OrderedObject.objects.create(id=counter, bool=True, number=counter)

        class OrderedObjectAdmin(admin.ModelAdmin):
            list_per_page = 10

        def check_results_order(ascending=False):
            custom_site.register(OrderedObject, OrderedObjectAdmin)
            model_admin = OrderedObjectAdmin(OrderedObject, custom_site)
            counter = 0 if ascending else 51
            for page in range(1, 6):
                request = self._mocked_authenticated_request(
                    "/orderedobject/?p=%s" % page, superuser
                )
                response = model_admin.changelist_view(request)
                for result in response.context_data["cl"].result_list:
                    counter += 1 if ascending else -1
                    self.assertEqual(result.id, counter)
            custom_site.unregister(OrderedObject)

        # When no order is defined at all, use the model's default ordering
        # (i.e. 'number').
        check_results_order(ascending=True)

        # When an order field is defined but multiple records have the same
        # value for that field, make sure everything gets ordered by -pk as
        # well.
        OrderedObjectAdmin.ordering = ["bool"]
        check_results_order()

        # When order fields are defined, including the pk itself, use them.
        OrderedObjectAdmin.ordering = ["bool", "-pk"]
        check_results_order()
        OrderedObjectAdmin.ordering = ["bool", "pk"]
        check_results_order(ascending=True)
        OrderedObjectAdmin.ordering = ["-id", "bool"]
        check_results_order()
        OrderedObjectAdmin.ordering = ["id", "bool"]
        check_results_order(ascending=True)
def check_results_order(ascending=False):
            custom_site.register(UnorderedObject, UnorderedObjectAdmin)
            model_admin = UnorderedObjectAdmin(UnorderedObject, custom_site)
            counter = 0 if ascending else 51
            for page in range(1, 6):
                request = self._mocked_authenticated_request(
                    "/unorderedobject/?p=%s" % page, superuser
                )
                response = model_admin.changelist_view(request)
                for result in response.context_data["cl"].result_list:
                    counter += 1 if ascending else -1
                    self.assertEqual(result.id, counter)
            custom_site.unregister(UnorderedObject)
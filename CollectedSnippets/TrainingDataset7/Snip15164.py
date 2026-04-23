def test_tuple_list_display(self):
        swallow = Swallow.objects.create(origin="Africa", load="12.34", speed="22.2")
        swallow2 = Swallow.objects.create(origin="Africa", load="12.34", speed="22.2")
        swallow_o2o = SwallowOneToOne.objects.create(swallow=swallow2)

        model_admin = SwallowAdmin(Swallow, custom_site)
        superuser = self._create_superuser("superuser")
        request = self._mocked_authenticated_request("/swallow/", superuser)
        response = model_admin.changelist_view(request)
        # just want to ensure it doesn't blow up during rendering
        self.assertContains(response, str(swallow.origin))
        self.assertContains(response, str(swallow.load))
        self.assertContains(response, str(swallow.speed))
        # Reverse one-to-one relations should work.
        self.assertContains(response, '<td class="field-swallowonetoone">-</td>')
        self.assertContains(
            response, '<td class="field-swallowonetoone">%s</td>' % swallow_o2o
        )
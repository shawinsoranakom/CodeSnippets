def test_disallowed_filtering(self):
        with self.assertLogs("django.security.DisallowedModelAdminLookup", "ERROR"):
            response = self.client.get(
                "%s?owner__email__startswith=fuzzy"
                % reverse("admin:admin_views_album_changelist")
            )
        self.assertEqual(response.status_code, 400)

        # Filters are allowed if explicitly included in list_filter
        response = self.client.get(
            "%s?color__value__startswith=red"
            % reverse("admin:admin_views_thing_changelist")
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "%s?color__value=red" % reverse("admin:admin_views_thing_changelist")
        )
        self.assertEqual(response.status_code, 200)

        # Filters should be allowed if they involve a local field without the
        # need to allow them in list_filter or date_hierarchy.
        response = self.client.get(
            "%s?age__gt=30" % reverse("admin:admin_views_person_changelist")
        )
        self.assertEqual(response.status_code, 200)

        e1 = Employee.objects.create(
            name="Anonymous", gender=1, age=22, alive=True, code="123"
        )
        e2 = Employee.objects.create(
            name="Visitor", gender=2, age=19, alive=True, code="124"
        )
        WorkHour.objects.create(datum=datetime.datetime.now(), employee=e1)
        WorkHour.objects.create(datum=datetime.datetime.now(), employee=e2)
        response = self.client.get(reverse("admin:admin_views_workhour_changelist"))
        self.assertContains(response, "employee__person_ptr__exact")
        response = self.client.get(
            "%s?employee__person_ptr__exact=%s"
            % (reverse("admin:admin_views_workhour_changelist"), e1.pk)
        )
        self.assertEqual(response.status_code, 200)
def test_non_field_errors(self):
        """
        Non-field errors are displayed for each of the forms in the
        changelist's formset.
        """
        fd1 = FoodDelivery.objects.create(
            reference="123", driver="bill", restaurant="thai"
        )
        fd2 = FoodDelivery.objects.create(
            reference="456", driver="bill", restaurant="india"
        )
        fd3 = FoodDelivery.objects.create(
            reference="789", driver="bill", restaurant="pizza"
        )

        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "3",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(fd1.id),
            "form-0-reference": "123",
            "form-0-driver": "bill",
            "form-0-restaurant": "thai",
            # Same data as above: Forbidden because of unique_together!
            "form-1-id": str(fd2.id),
            "form-1-reference": "456",
            "form-1-driver": "bill",
            "form-1-restaurant": "thai",
            "form-2-id": str(fd3.id),
            "form-2-reference": "789",
            "form-2-driver": "bill",
            "form-2-restaurant": "pizza",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_fooddelivery_changelist"), data
        )
        self.assertContains(
            response,
            '<tr><td colspan="4"><ul class="errorlist nonfield"><li>Food delivery '
            "with this Driver and Restaurant already exists.</li></ul></td></tr>",
            1,
            html=True,
        )

        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "3",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(fd1.id),
            "form-0-reference": "123",
            "form-0-driver": "bill",
            "form-0-restaurant": "thai",
            # Same data as above: Forbidden because of unique_together!
            "form-1-id": str(fd2.id),
            "form-1-reference": "456",
            "form-1-driver": "bill",
            "form-1-restaurant": "thai",
            # Same data also.
            "form-2-id": str(fd3.id),
            "form-2-reference": "789",
            "form-2-driver": "bill",
            "form-2-restaurant": "thai",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_fooddelivery_changelist"), data
        )
        self.assertContains(
            response,
            '<tr><td colspan="4"><ul class="errorlist nonfield"><li>Food delivery '
            "with this Driver and Restaurant already exists.</li></ul></td></tr>",
            2,
            html=True,
        )
def test_allowed_filtering_15103(self):
        """
        Regressions test for ticket 15103 - filtering on fields defined in a
        ForeignKey 'limit_choices_to' should be allowed, otherwise
        raw_id_fields can break.
        """
        # Filters should be allowed if they are defined on a ForeignKey
        # pointing to this model.
        url = "%s?leader__name=Palin&leader__age=27" % reverse(
            "admin:admin_views_inquisition_changelist"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
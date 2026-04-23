def test_to_field_resolution_with_mti(self):
        """
        to_field resolution should correctly resolve for target models using
        MTI. Tests for single and multi-level cases.
        """
        tests = [
            (Employee, WorkHour, "employee"),
            (Manager, Bonus, "recipient"),
        ]
        for Target, Remote, related_name in tests:
            with self.subTest(
                target_model=Target, remote_model=Remote, related_name=related_name
            ):
                o = Target.objects.create(
                    name="Frida Kahlo", gender=2, code="painter", alive=False
                )
                opts = {
                    "app_label": Remote._meta.app_label,
                    "model_name": Remote._meta.model_name,
                    "field_name": related_name,
                }
                request = self.factory.get(self.url, {"term": "frida", **opts})
                request.user = self.superuser
                response = AutocompleteJsonView.as_view(**self.as_view_args)(request)
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.text)
                self.assertEqual(
                    data,
                    {
                        "results": [{"id": str(o.pk), "text": o.name}],
                        "pagination": {"more": False},
                    },
                )
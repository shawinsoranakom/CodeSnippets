def test_log_deletions(self):
        ma = ModelAdmin(Band, self.site)
        mock_request = MockRequest()
        mock_request.user = User.objects.create(username="akash")
        content_type = get_content_type_for_model(self.band)
        Band.objects.create(
            name="The Beatles",
            bio="A legendary rock band from Liverpool.",
            sign_date=date(1962, 1, 1),
        )
        Band.objects.create(
            name="Mohiner Ghoraguli",
            bio="A progressive rock band from Calcutta.",
            sign_date=date(1975, 1, 1),
        )
        queryset = Band.objects.all().order_by("-id")[:3]
        self.assertEqual(len(queryset), 3)
        with self.assertNumQueries(1):
            ma.log_deletions(mock_request, queryset)
        logs = (
            LogEntry.objects.filter(action_flag=DELETION)
            .order_by("id")
            .values_list(
                "user_id",
                "content_type",
                "object_id",
                "object_repr",
                "action_flag",
                "change_message",
            )
        )
        expected_log_values = [
            (
                mock_request.user.id,
                content_type.id,
                str(obj.pk),
                str(obj),
                DELETION,
                "",
            )
            for obj in queryset
        ]
        self.assertSequenceEqual(logs, expected_log_values)
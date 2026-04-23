def test_log_actions(self):
        queryset = Article.objects.all().order_by("-id")
        msg = "Deleted Something"
        content_type = ContentType.objects.get_for_model(self.a1)
        self.assertEqual(len(queryset), 3)
        with self.assertNumQueries(1):
            result = LogEntry.objects.log_actions(
                self.user.pk,
                queryset,
                DELETION,
                change_message=msg,
            )
        self.assertEqual(len(result), len(queryset))
        logs = (
            LogEntry.objects.filter(action_flag=DELETION)
            .order_by("id")
            .values_list(
                "user",
                "content_type",
                "object_id",
                "object_repr",
                "action_flag",
                "change_message",
            )
        )
        expected_log_values = [
            (
                self.user.pk,
                content_type.id,
                str(obj.pk),
                str(obj),
                DELETION,
                msg,
            )
            for obj in queryset
        ]
        result_logs = [
            (
                entry.user_id,
                entry.content_type_id,
                str(entry.object_id),
                entry.object_repr,
                entry.action_flag,
                entry.change_message,
            )
            for entry in result
        ]
        self.assertSequenceEqual(logs, result_logs)
        self.assertSequenceEqual(logs, expected_log_values)
        self.assertEqual(self.signals, [])
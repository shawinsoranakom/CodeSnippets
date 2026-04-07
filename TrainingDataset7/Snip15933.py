def test_log_actions_single_object_param(self):
        queryset = Article.objects.filter(pk=self.a1.pk)
        msg = "Deleted Something"
        content_type = ContentType.objects.get_for_model(self.a1)
        self.assertEqual(len(queryset), 1)
        for single_object in (True, False):
            self.signals = []
            with self.subTest(single_object=single_object), self.assertNumQueries(1):
                result = LogEntry.objects.log_actions(
                    self.user.pk,
                    queryset,
                    DELETION,
                    change_message=msg,
                    single_object=single_object,
                )
                if single_object:
                    self.assertIsInstance(result, LogEntry)
                    entry = result
                else:
                    self.assertIsInstance(result, list)
                    self.assertEqual(len(result), 1)
                    entry = result[0]
                self.assertEqual(entry.user_id, self.user.pk)
                self.assertEqual(entry.content_type_id, content_type.id)
                self.assertEqual(str(entry.object_id), str(self.a1.pk))
                self.assertEqual(entry.object_repr, str(self.a1))
                self.assertEqual(entry.action_flag, DELETION)
                self.assertEqual(entry.change_message, msg)
                expected_signals = [
                    ("pre_save", entry),
                    ("post_save", entry, True),
                ]
                self.assertEqual(self.signals, expected_signals)
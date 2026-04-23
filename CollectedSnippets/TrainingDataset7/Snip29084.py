def test_log_actions(self):
        ma = ModelAdmin(Band, self.site)
        mock_request = MockRequest()
        mock_request.user = User.objects.create(username="bill")
        content_type = get_content_type_for_model(self.band)
        tests = (
            (ma.log_addition, ADDITION, {"added": {}}),
            (ma.log_change, CHANGE, {"changed": {"fields": ["name", "bio"]}}),
        )
        for method, flag, message in tests:
            with self.subTest(name=method.__name__):
                created = method(mock_request, self.band, message)
                fetched = LogEntry.objects.filter(action_flag=flag).latest("id")
                self.assertEqual(created, fetched)
                self.assertEqual(fetched.action_flag, flag)
                self.assertEqual(fetched.content_type, content_type)
                self.assertEqual(fetched.object_id, str(self.band.pk))
                self.assertEqual(fetched.user, mock_request.user)
                self.assertEqual(fetched.change_message, str(message))
                self.assertEqual(fetched.object_repr, str(self.band))
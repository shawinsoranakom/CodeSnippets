def assertPushNotification(self, mail_push_count=0,
                               endpoint=None, keys=None,
                               title=None, title_content=None, body=None, body_content=None,
                               options=None):
        """ Asserts a single push notification (not really batch enabled currently) """
        self.push_to_end_point_mocked.assert_called_once()
        self.assertEqual(self.env['mail.push'].search_count([]), mail_push_count)
        if endpoint:
            self.assertEqual(self.push_to_end_point_mocked.call_args.kwargs['device']['endpoint'], endpoint)
        if keys:
            private, public = keys
            self.assertIn(private, self.push_to_end_point_mocked.call_args.kwargs)
            self.assertIn(public, self.push_to_end_point_mocked.call_args.kwargs)
        payload_value = json.loads(self.push_to_end_point_mocked.call_args.kwargs['payload'])
        if title_content:
            self.assertIn(title_content, payload_value['title'])
        elif title:
            self.assertEqual(title, payload_value['title'])
        if body_content:
            self.assertIn(body_content, payload_value['options']['body'])
        elif body:
            self.assertEqual(body, payload_value['options']['body'])
        if options:
            payload_options = payload_value['options']
            for key, val in options.items():
                with self.subTest(key=key):
                    self.assertEqual(payload_options[key], val)
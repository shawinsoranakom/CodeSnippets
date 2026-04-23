def test_alternatives(self):
        msg = EmailMultiAlternatives()
        html_content = "<p>This is <strong>html</strong></p>"
        mime_type = "text/html"
        msg.attach_alternative(html_content, mime_type)

        self.assertIsInstance(msg.alternatives[0], EmailAlternative)

        self.assertEqual(msg.alternatives[0][0], html_content)
        self.assertEqual(msg.alternatives[0].content, html_content)

        self.assertEqual(msg.alternatives[0][1], mime_type)
        self.assertEqual(msg.alternatives[0].mimetype, mime_type)

        self.assertIn(html_content, msg.message().as_string())
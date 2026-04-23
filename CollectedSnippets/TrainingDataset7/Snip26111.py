def test_alternatives_and_attachment_serializable(self):
        html_content = "<p>This is <strong>html</strong></p>"
        mime_type = "text/html"

        msg = EmailMultiAlternatives(alternatives=[(html_content, mime_type)])
        msg.attach("test.txt", "This is plain text.", "plain/text")

        # Alternatives and attachments can be serialized.
        restored = pickle.loads(pickle.dumps(msg))

        self.assertEqual(restored.subject, msg.subject)
        self.assertEqual(restored.body, msg.body)
        self.assertEqual(restored.from_email, msg.from_email)
        self.assertEqual(restored.to, msg.to)
        self.assertEqual(restored.alternatives, msg.alternatives)
        self.assertEqual(restored.attachments, msg.attachments)
def subtype_as_add(self, method, subtype, outcome):
        m, msg_headers, payload = self._make_subtype_test_message(subtype)
        cm = self._TestSetContentManager()
        add_method = 'add_attachment' if method=='mixed' else 'add_' + method
        if outcome == 'raises':
            self._check_disallowed_subtype_raises(m, method, subtype, add_method)
            return
        getattr(m, add_method)('test', content_manager=cm)
        self.assertEqual(m.get_content_maintype(), 'multipart')
        self.assertEqual(m.get_content_subtype(), method)
        if method == subtype or subtype == 'no_content':
            self.assertEqual(len(m.get_payload()), 1)
            for name, value in msg_headers:
                self.assertEqual(m[name], value)
            part = m.get_payload()[0]
        else:
            self.assertEqual(len(m.get_payload()), 2)
            self._check_make_multipart(m, msg_headers, payload)
            part = m.get_payload()[1]
        self.assertEqual(part.get_content_type(), 'text/plain')
        self.assertEqual(part.get_payload(), 'test')
        if method=='mixed':
            self.assertEqual(part['Content-Disposition'], 'attachment')
        elif method=='related':
            self.assertEqual(part['Content-Disposition'], 'inline')
        else:
            # Otherwise we don't guess.
            self.assertIsNone(part['Content-Disposition'])
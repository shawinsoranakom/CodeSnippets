def content_type_as_value(self,
                              source,
                              content_type,
                              maintype,
                              subtype,
                              *args):
        l = len(args)
        parmdict = args[0] if l>0 else {}
        defects =  args[1] if l>1 else []
        decoded =  args[2] if l>2 and args[2] is not DITTO else source
        header = 'Content-Type:' + ' ' if source else ''
        folded = args[3] if l>3 else header + decoded + '\n'
        # Both rfc2231 test cases with utf-8%E2%80%9D raise warnings,
        # clear encoding cache to ensure test isolation.
        if 'utf-8%E2%80%9D' in source and 'ascii' not in source:
            import encodings
            encodings._cache.clear()
            with warnings_helper.check_warnings(('', DeprecationWarning)):
                h = self.make_header('Content-Type', source)
        else:
            h = self.make_header('Content-Type', source)
        self.assertEqual(h.content_type, content_type)
        self.assertEqual(h.maintype, maintype)
        self.assertEqual(h.subtype, subtype)
        self.assertEqual(h.params, parmdict)
        with self.assertRaises(TypeError):
            h.params['abc'] = 'xyz'   # make sure params is read-only.
        self.assertDefectsEqual(h.defects, defects)
        self.assertEqual(h, decoded)
        self.assertEqual(h.fold(policy=policy.default), folded)
def test_wm_attribute(self):
        w = self.root
        attributes = w.wm_attributes(return_python_dict=True)
        self.assertIsInstance(attributes, dict)
        attributes2 = w.wm_attributes()
        self.assertIsInstance(attributes2, tuple)
        self.assertEqual(attributes2[::2],
                         tuple('-' + k for k in attributes))
        self.assertEqual(attributes2[1::2], tuple(attributes.values()))
        # silently deprecated
        attributes3 = w.wm_attributes(None)
        if self.wantobjects:
            self.assertEqual(attributes3, attributes2)
        else:
            self.assertIsInstance(attributes3, str)

        for name in attributes:
            self.assertEqual(w.wm_attributes(name), attributes[name])
        # silently deprecated
        for name in attributes:
            self.assertEqual(w.wm_attributes('-' + name), attributes[name])

        self.assertIn('alpha', attributes)
        self.assertIn('fullscreen', attributes)
        self.assertIn('topmost', attributes)
        if w._windowingsystem == "win32":
            self.assertIn('disabled', attributes)
            self.assertIn('toolwindow', attributes)
            self.assertIn('transparentcolor', attributes)
        if w._windowingsystem == "aqua":
            self.assertIn('modified', attributes)
            self.assertIn('notify', attributes)
            self.assertIn('titlepath', attributes)
            self.assertIn('transparent', attributes)
        if w._windowingsystem == "x11":
            self.assertIn('type', attributes)
            self.assertIn('zoomed', attributes)

        w.wm_attributes(alpha=0.5)
        self.assertEqual(w.wm_attributes('alpha'),
                         0.5 if self.wantobjects else '0.5')
        w.wm_attributes(alpha=1.0)
        self.assertEqual(w.wm_attributes('alpha'),
                         1.0 if self.wantobjects else '1.0')
        # silently deprecated
        w.wm_attributes('-alpha', 0.5)
        self.assertEqual(w.wm_attributes('alpha'),
                         0.5 if self.wantobjects else '0.5')
        w.wm_attributes(alpha=1.0)
        self.assertEqual(w.wm_attributes('alpha'),
                         1.0 if self.wantobjects else '1.0')
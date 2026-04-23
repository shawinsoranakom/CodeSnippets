def test_configure_custom_copy(self):
        style = self.style

        curr_theme = self.style.theme_use()
        self.addCleanup(self.style.theme_use, curr_theme)
        for theme in self.style.theme_names():
            self.style.theme_use(theme)
            for name in CLASS_NAMES:
                default = style.configure(name)
                if not default:
                    continue
                with self.subTest(theme=theme, name=name):
                    if support.verbose >= 2:
                        print('configure', theme, name, default)
                    if (theme in ('vista', 'xpnative')
                            and sys.getwindowsversion()[:2] == (6, 1)):
                        # Fails on the Windows 7 buildbot
                        continue
                    newname = f'C.{name}'
                    self.assertEqual(style.configure(newname), None)
                    style.configure(newname, **default)
                    self.assertEqual(style.configure(newname), default)
                    for key, value in default.items():
                        self.assertEqual(style.configure(newname, key), value)
def test_no_dirs_accidentally_skipped(self):
        os_walk_results = [
            # To discover .po filepaths, compilemessages uses with a starting
            # list of basedirs to inspect, which in this scenario are:
            #   ["conf/locale", "locale"]
            # Then os.walk is used to discover other locale dirs, ignoring dirs
            # matching `ignore_patterns`. Mock the results to place an ignored
            # directory directly before and after a directory named "locale".
            [("somedir", ["ignore", "locale", "ignore"], [])],
            # This will result in three basedirs discovered:
            #   ["conf/locale", "locale", "somedir/locale"]
            # os.walk is called for each locale in each basedir looking for .po
            # files. In this scenario, we need to mock os.walk results for
            # "en", "fr", and "it" locales for each basedir:
            [("exclude/locale/LC_MESSAGES", [], ["en.po"])],
            [("exclude/locale/LC_MESSAGES", [], ["fr.po"])],
            [("exclude/locale/LC_MESSAGES", [], ["it.po"])],
            [("exclude/conf/locale/LC_MESSAGES", [], ["en.po"])],
            [("exclude/conf/locale/LC_MESSAGES", [], ["fr.po"])],
            [("exclude/conf/locale/LC_MESSAGES", [], ["it.po"])],
            [("exclude/somedir/locale/LC_MESSAGES", [], ["en.po"])],
            [("exclude/somedir/locale/LC_MESSAGES", [], ["fr.po"])],
            [("exclude/somedir/locale/LC_MESSAGES", [], ["it.po"])],
        ]

        module_path = "django.core.management.commands.compilemessages"
        with mock.patch(f"{module_path}.os.walk", side_effect=os_walk_results):
            with mock.patch(f"{module_path}.os.path.isdir", return_value=True):
                with mock.patch(
                    f"{module_path}.Command.compile_messages"
                ) as mock_compile_messages:
                    call_command("compilemessages", ignore=["ignore"], verbosity=4)

        expected = [
            (
                [
                    ("exclude/locale/LC_MESSAGES", "en.po"),
                    ("exclude/locale/LC_MESSAGES", "fr.po"),
                    ("exclude/locale/LC_MESSAGES", "it.po"),
                ],
            ),
            (
                [
                    ("exclude/conf/locale/LC_MESSAGES", "en.po"),
                    ("exclude/conf/locale/LC_MESSAGES", "fr.po"),
                    ("exclude/conf/locale/LC_MESSAGES", "it.po"),
                ],
            ),
            (
                [
                    ("exclude/somedir/locale/LC_MESSAGES", "en.po"),
                    ("exclude/somedir/locale/LC_MESSAGES", "fr.po"),
                    ("exclude/somedir/locale/LC_MESSAGES", "it.po"),
                ],
            ),
        ]
        self.assertEqual([c.args for c in mock_compile_messages.mock_calls], expected)
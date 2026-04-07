def _test_optgroups(self, choices):
        groups = list(
            self.widget(choices=choices).optgroups(
                "name",
                ["vhs"],
                attrs={"class": "super"},
            )
        )
        audio, video, unknown = groups
        label, options, index = audio
        self.assertEqual(label, "Audio")
        self.assertEqual(
            options,
            [
                {
                    "value": "vinyl",
                    "type": "select",
                    "attrs": {},
                    "index": "0_0",
                    "label": "Vinyl",
                    "template_name": "django/forms/widgets/select_option.html",
                    "name": "name",
                    "selected": False,
                    "wrap_label": True,
                },
                {
                    "value": "cd",
                    "type": "select",
                    "attrs": {},
                    "index": "0_1",
                    "label": "CD",
                    "template_name": "django/forms/widgets/select_option.html",
                    "name": "name",
                    "selected": False,
                    "wrap_label": True,
                },
            ],
        )
        self.assertEqual(index, 0)
        label, options, index = video
        self.assertEqual(label, "Video")
        self.assertEqual(
            options,
            [
                {
                    "value": "vhs",
                    "template_name": "django/forms/widgets/select_option.html",
                    "label": "VHS Tape",
                    "attrs": {"selected": True},
                    "index": "1_0",
                    "name": "name",
                    "selected": True,
                    "type": "select",
                    "wrap_label": True,
                },
                {
                    "value": "dvd",
                    "template_name": "django/forms/widgets/select_option.html",
                    "label": "DVD",
                    "attrs": {},
                    "index": "1_1",
                    "name": "name",
                    "selected": False,
                    "type": "select",
                    "wrap_label": True,
                },
            ],
        )
        self.assertEqual(index, 1)
        label, options, index = unknown
        self.assertIsNone(label)
        self.assertEqual(
            options,
            [
                {
                    "value": "unknown",
                    "selected": False,
                    "template_name": "django/forms/widgets/select_option.html",
                    "label": "Unknown",
                    "attrs": {},
                    "index": "2",
                    "name": "name",
                    "type": "select",
                    "wrap_label": True,
                }
            ],
        )
        self.assertEqual(index, 2)
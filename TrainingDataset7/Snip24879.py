def test_inflection_for_timedelta(self):
        """
        Translation of '%d day'/'%d month'/… may differ depending on the
        context of the string it is inserted in.
        """
        test_list = [
            # "%(delta)s ago" translations
            now - datetime.timedelta(days=1),
            now - datetime.timedelta(days=2),
            now - datetime.timedelta(days=30),
            now - datetime.timedelta(days=60),
            now - datetime.timedelta(days=500),
            now - datetime.timedelta(days=865),
            # "%(delta)s from now" translations
            now + datetime.timedelta(days=1),
            now + datetime.timedelta(days=2),
            now + datetime.timedelta(days=31),
            now + datetime.timedelta(days=61),
            now + datetime.timedelta(days=500),
            now + datetime.timedelta(days=865),
        ]
        result_list = [
            "před 1\xa0dnem",
            "před 2\xa0dny",
            "před 1\xa0měsícem",
            "před 2\xa0měsíci",
            "před 1\xa0rokem, 4\xa0měsíci",
            "před 2\xa0lety, 4\xa0měsíci",
            "za 1\xa0den",
            "za 2\xa0dny",
            "za 1\xa0měsíc",
            "za 2\xa0měsíce",
            "za 1\xa0rok, 4\xa0měsíce",
            "za 2\xa0roky, 4\xa0měsíce",
        ]

        orig_humanize_datetime, humanize.datetime = humanize.datetime, MockDateTime
        try:
            # Choose a language with different
            # naturaltime-past/naturaltime-future translations.
            with translation.override("cs"):
                self.humanize_tester(test_list, result_list, "naturaltime")
        finally:
            humanize.datetime = orig_humanize_datetime
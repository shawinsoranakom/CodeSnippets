def test_naturalday(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        someday = today - datetime.timedelta(days=10)
        notdate = "I'm not a date value"

        test_list = (today, yesterday, tomorrow, someday, notdate, None)
        someday_result = defaultfilters.date(someday)
        result_list = (
            _("today"),
            _("yesterday"),
            _("tomorrow"),
            someday_result,
            "I'm not a date value",
            None,
        )
        self.humanize_tester(test_list, result_list, "naturalday")
def test_no_log_when_variable_exists(self):
        with self.assertNoLogs("django.template", self.loglevel):
            Variable("article.section").resolve({"article": {"section": "News"}})
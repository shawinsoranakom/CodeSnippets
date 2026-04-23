def test_log_on_variable_does_not_exist_not_silent(self):
        with self.assertLogs("django.template", self.loglevel) as cm:
            with self.assertRaises(VariableDoesNotExist):
                Variable("article.author").resolve({"article": {"section": "News"}})

        self.assertEqual(len(cm.records), 1)
        log_record = cm.records[0]
        self.assertEqual(
            log_record.getMessage(),
            "Exception while resolving variable 'author' in template 'unknown'.",
        )
        self.assertIsNotNone(log_record.exc_info)
        raised_exception = log_record.exc_info[1]
        self.assertEqual(
            str(raised_exception),
            "Failed lookup for key [author] in {'section': 'News'}",
        )
def assertLogRecord(
        self,
        logger_cm,
        msg,
        levelno,
        status_code,
        request=None,
        exc_class=None,
    ):
        self.assertEqual(
            records_len := len(logger_cm.records),
            1,
            f"Wrong number of calls for {logger_cm=} in {levelno=} (expected 1, got "
            f"{records_len}).",
        )
        record = logger_cm.records[0]
        self.assertEqual(record.getMessage(), msg)
        self.assertEqual(record.levelno, levelno)
        self.assertEqual(record.status_code, status_code)
        if request is not None:
            self.assertEqual(record.request, request)
        if exc_class:
            self.assertIsNotNone(record.exc_info)
            self.assertEqual(record.exc_info[0], exc_class)
        return record
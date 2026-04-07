def assertForbiddenReason(
        self, response, logger_cm, reason, levelno=logging.WARNING
    ):
        self.assertEqual(
            records_len := len(logger_cm.records),
            1,
            f"Unexpected number of records for {logger_cm=} in {levelno=} (expected 1, "
            f"got {records_len}).",
        )
        record = logger_cm.records[0]
        self.assertEqual(record.getMessage(), "Forbidden (%s): " % reason)
        self.assertEqual(record.levelno, levelno)
        self.assertEqual(record.status_code, 403)
        self.assertEqual(response.status_code, 403)
def test_default_item_completed(self):
        item = {"name": "name"}
        assert self.pipe.item_completed([], item, self.info) is item

        # Check that failures are logged by default
        fail = Failure(Exception())
        results = [(True, 1), (False, fail)]

        with LogCapture() as log:
            new_item = self.pipe.item_completed(results, item, self.info)

        assert new_item is item
        assert len(log.records) == 1
        record = log.records[0]
        assert record.levelname == "ERROR"
        assert record.exc_info == failure_to_exc_info(fail)

        # disable failure logging and check again
        self.pipe.LOG_FAILED_RESULTS = False
        with LogCapture() as log:
            new_item = self.pipe.item_completed(results, item, self.info)
        assert new_item is item
        assert len(log.records) == 0
def test_skip_locked_skips_locked_rows(self):
        """
        If skip_locked is specified, the locked row is skipped resulting in
        Person.DoesNotExist.
        """
        self.start_blocking_transaction()
        status = []
        thread = threading.Thread(
            target=self.run_select_for_update,
            args=(status,),
            kwargs={"skip_locked": True},
        )
        thread.start()
        time.sleep(1)
        thread.join()
        self.end_blocking_transaction()
        self.assertIsInstance(status[-1], Person.DoesNotExist)
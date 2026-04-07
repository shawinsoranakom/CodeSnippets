def test_nowait_raises_error_on_block(self):
        """
        If nowait is specified, we expect an error to be raised rather
        than blocking.
        """
        self.start_blocking_transaction()
        status = []

        thread = threading.Thread(
            target=self.run_select_for_update,
            args=(status,),
            kwargs={"nowait": True},
        )

        thread.start()
        time.sleep(1)
        thread.join()
        self.end_blocking_transaction()
        self.assertIsInstance(status[-1], DatabaseError)
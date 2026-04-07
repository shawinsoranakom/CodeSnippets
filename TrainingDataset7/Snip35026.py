def test_buffer_mode_reports_setupclass_failure(self):
        test = SampleErrorTest("dummy_test")
        remote_result = RemoteTestResult()
        suite = TestSuite([test])
        suite.run(remote_result)

        pts = ParallelTestSuite([suite], processes=2, buffer=True)
        pts.serialized_aliases = set()
        test_result = TestResult()
        test_result.buffer = True

        with unittest.mock.patch("multiprocessing.Pool") as mock_pool:

            def fake_next(*args, **kwargs):
                test_result.shouldStop = True
                return (0, remote_result.events)

            mock_imap = mock_pool.return_value.__enter__.return_value.imap_unordered
            mock_imap.return_value = unittest.mock.Mock(next=fake_next)
            pts.run(test_result)

        self.assertIn("ValueError: woops", test_result.errors[0][1])
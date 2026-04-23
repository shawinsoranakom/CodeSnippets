def test_simple_enqueue(self):
        """Enqueue a single ForwardMsg."""
        rq = ForwardMsgQueue()
        self.assertTrue(rq.is_empty())

        rq.enqueue(NEW_SESSION_MSG)

        self.assertFalse(rq.is_empty())
        queue = rq.flush()
        self.assertTrue(rq.is_empty())
        self.assertEqual(1, len(queue))
        self.assertTrue(queue[0].new_session.config.allow_run_on_save)
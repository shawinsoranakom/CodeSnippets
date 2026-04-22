def test_enqueue_two(self):
        """Enqueue two ForwardMsgs."""
        rq = ForwardMsgQueue()
        self.assertTrue(rq.is_empty())

        rq.enqueue(NEW_SESSION_MSG)

        TEXT_DELTA_MSG1.metadata.delta_path[:] = make_delta_path(
            RootContainer.MAIN, (), 0
        )
        rq.enqueue(TEXT_DELTA_MSG1)

        queue = rq.flush()
        self.assertEqual(2, len(queue))
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 0), queue[1].metadata.delta_path
        )
        self.assertEqual("text1", queue[1].delta.new_element.text.body)
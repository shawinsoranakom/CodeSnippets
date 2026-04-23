def test_enqueue_three(self):
        """Enqueue 3 ForwardMsgs."""
        rq = ForwardMsgQueue()
        self.assertTrue(rq.is_empty())

        rq.enqueue(NEW_SESSION_MSG)

        TEXT_DELTA_MSG1.metadata.delta_path[:] = make_delta_path(
            RootContainer.MAIN, (), 0
        )
        rq.enqueue(TEXT_DELTA_MSG1)

        TEXT_DELTA_MSG2.metadata.delta_path[:] = make_delta_path(
            RootContainer.MAIN, (), 1
        )
        rq.enqueue(TEXT_DELTA_MSG2)

        queue = rq.flush()
        self.assertEqual(3, len(queue))
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 0), queue[1].metadata.delta_path
        )
        self.assertEqual("text1", queue[1].delta.new_element.text.body)
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 1), queue[2].metadata.delta_path
        )
        self.assertEqual("text2", queue[2].delta.new_element.text.body)
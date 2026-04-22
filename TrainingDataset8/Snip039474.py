def test_replace_element(self):
        """Enqueuing an element with the same delta_path as another element
        already in the queue should replace the original element.
        """
        rq = ForwardMsgQueue()
        self.assertTrue(rq.is_empty())

        rq.enqueue(NEW_SESSION_MSG)

        TEXT_DELTA_MSG1.metadata.delta_path[:] = make_delta_path(
            RootContainer.MAIN, (), 0
        )
        rq.enqueue(TEXT_DELTA_MSG1)

        TEXT_DELTA_MSG2.metadata.delta_path[:] = make_delta_path(
            RootContainer.MAIN, (), 0
        )
        rq.enqueue(TEXT_DELTA_MSG2)

        queue = rq.flush()
        self.assertEqual(2, len(queue))
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 0), queue[1].metadata.delta_path
        )
        self.assertEqual("text2", queue[1].delta.new_element.text.body)
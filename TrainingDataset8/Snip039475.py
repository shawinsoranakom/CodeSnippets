def test_dont_replace_block(self, other_msg: ForwardMsg):
        """add_block deltas should never be replaced because they can
        have dependent deltas later in the queue."""
        rq = ForwardMsgQueue()
        self.assertTrue(rq.is_empty())

        ADD_BLOCK_MSG.metadata.delta_path[:] = make_delta_path(
            RootContainer.MAIN, (), 0
        )

        other_msg.metadata.delta_path[:] = make_delta_path(RootContainer.MAIN, (), 0)

        # Delta messages should not replace `add_block` deltas with the
        # same delta_path.
        rq.enqueue(ADD_BLOCK_MSG)
        rq.enqueue(other_msg)
        queue = rq.flush()
        self.assertEqual(2, len(queue))
        self.assertEqual(ADD_BLOCK_MSG, queue[0])
        self.assertEqual(other_msg, queue[1])
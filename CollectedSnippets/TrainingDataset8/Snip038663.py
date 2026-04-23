def test_enqueue_same_id(self):
        cursor = LockedCursor(root_container=RootContainer.MAIN, index=123)
        dg = DeltaGenerator(root_container=RootContainer.MAIN, cursor=cursor)
        self.assertEqual(123, dg._cursor.index)

        test_data = "some test data"
        text_proto = TextProto()
        text_proto.body = test_data
        new_dg = dg._enqueue("text", text_proto)

        self.assertEqual(dg._cursor, new_dg._cursor)

        msg = self.get_message_from_queue()
        # The last element in delta_path is the delta's index in its container.
        self.assertEqual(
            make_delta_path(RootContainer.MAIN, (), 123), msg.metadata.delta_path
        )
        self.assertEqual(msg.delta.new_element.text.body, test_data)
def test_tags_fwd_msgs_with_last_backmsg_id_if_set(self):
        session = _create_test_session()
        session._debug_last_backmsg_id = "some backmsg id"

        msg = ForwardMsg()
        session._enqueue_forward_msg(msg)

        self.assertEqual(msg.debug_last_backmsg_id, "some backmsg id")
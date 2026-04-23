async def test_handle_backmsg_handles_debug_ids(self):
        session = _create_test_session(asyncio.get_running_loop())
        msg = BackMsg(
            rerun_script=session._client_state, debug_last_backmsg_id="some backmsg"
        )
        session.handle_backmsg(msg)
        self.assertEqual(session._debug_last_backmsg_id, "some backmsg")
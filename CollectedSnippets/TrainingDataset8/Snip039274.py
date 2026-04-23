async def test_handle_backmsg_handles_exceptions(self):
        """Exceptions raised in handle_backmsg should be sent to
        handle_backmsg_exception.
        """
        session = _create_test_session(asyncio.get_running_loop())
        with patch.object(
            session, "handle_backmsg_exception"
        ) as handle_backmsg_exception, patch.object(
            session, "_handle_clear_cache_request"
        ) as handle_clear_cache_request:

            error = Exception("explode!")
            handle_clear_cache_request.side_effect = error

            msg = BackMsg()
            msg.clear_cache = True
            session.handle_backmsg(msg)

            handle_clear_cache_request.assert_called_once()
            handle_backmsg_exception.assert_called_once_with(error)
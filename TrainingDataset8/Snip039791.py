def enqueue_forward_msg(self, session_id: str, msg: ForwardMsg) -> None:
        """Enqueue a ForwardMsg to a given session_id. It will be sent
        to the client on the next iteration through the run loop. (You can
        use `await self.tick_runtime_loop()` to tick the run loop.)
        """
        session_info = self.runtime._get_session_info(session_id)
        if session_info is None:
            return
        session_info.session._enqueue_forward_msg(msg)
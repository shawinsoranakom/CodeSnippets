def _send_message(self, session_info: SessionInfo, msg: ForwardMsg) -> None:
        """Send a message to a client.

        If the client is likely to have already cached the message, we may
        instead send a "reference" message that contains only the hash of the
        message.

        Parameters
        ----------
        session_info : SessionInfo
            The SessionInfo associated with websocket
        msg : ForwardMsg
            The message to send to the client

        Notes
        -----
        Threading: UNSAFE. Must be called on the eventloop thread.
        """
        msg.metadata.cacheable = is_cacheable_msg(msg)
        msg_to_send = msg
        if msg.metadata.cacheable:
            populate_hash_if_needed(msg)

            if self._message_cache.has_message_reference(
                msg, session_info.session, session_info.script_run_count
            ):
                # This session has probably cached this message. Send
                # a reference instead.
                LOGGER.debug("Sending cached message ref (hash=%s)", msg.hash)
                msg_to_send = create_reference_msg(msg)

            # Cache the message so it can be referenced in the future.
            # If the message is already cached, this will reset its
            # age.
            LOGGER.debug("Caching message (hash=%s)", msg.hash)
            self._message_cache.add_message(
                msg, session_info.session, session_info.script_run_count
            )

        # If this was a `script_finished` message, we increment the
        # script_run_count for this session, and update the cache
        if (
            msg.WhichOneof("type") == "script_finished"
            and msg.script_finished == ForwardMsg.FINISHED_SUCCESSFULLY
        ):
            LOGGER.debug(
                "Script run finished successfully; "
                "removing expired entries from MessageCache "
                "(max_age=%s)",
                config.get_option("global.maxCachedMessageAge"),
            )
            session_info.script_run_count += 1
            self._message_cache.remove_expired_session_entries(
                session_info.session, session_info.script_run_count
            )

        # Ship it off!
        session_info.client.write_forward_msg(msg_to_send)
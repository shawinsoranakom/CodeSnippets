async def update_message_feedback(chat_id, session_id, msg_id):
    owned = _ensure_owned_chat(chat_id)
    if not owned:
        return get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
    try:
        req = await get_request_json()
        ok, conv = ConversationService.get_by_id(session_id)
        if not ok or conv.dialog_id != chat_id:
            return get_data_error_result(message="Session not found!")
        thumb_raw = req.get("thumbup")
        if not isinstance(thumb_raw, bool):
            return get_data_error_result(message="thumbup must be a boolean")
        feedback = req.get("feedback", "")
        conv_dict = conv.to_dict()
        message_index = None
        apply_chunk_feedback = False
        prior_thumb = None
        for i, msg in enumerate(conv_dict["message"]):
            if msg_id == msg.get("id", "") and msg.get("role", "") == "assistant":
                prior_thumb = msg.get("thumbup")
                if thumb_raw is True:
                    msg["thumbup"] = True
                    msg.pop("feedback", None)
                    apply_chunk_feedback = prior_thumb is not True
                else:
                    msg["thumbup"] = False
                    if feedback:
                        msg["feedback"] = feedback
                    apply_chunk_feedback = prior_thumb is not False
                message_index = i
                break

        if message_index is not None and apply_chunk_feedback:
            try:
                ref_index = (message_index - 1) // 2
                if 0 <= ref_index < len(conv_dict.get("reference", [])):
                    reference = conv_dict["reference"][ref_index]
                    if reference:
                        if isinstance(prior_thumb, bool) and prior_thumb != thumb_raw:
                            ChunkFeedbackService.apply_feedback(
                                tenant_id=current_user.id,
                                reference=reference,
                                is_positive=not prior_thumb,
                            )
                        feedback_result = ChunkFeedbackService.apply_feedback(
                            tenant_id=current_user.id,
                            reference=reference,
                            is_positive=thumb_raw is True,
                        )
                        logging.debug(
                            "Chunk feedback applied: %s succeeded, %s failed",
                            feedback_result["success_count"],
                            feedback_result["fail_count"],
                        )
            except Exception as e:
                logging.warning("Failed to apply chunk feedback: %s", e)

        ConversationService.update_by_id(conv_dict["id"], conv_dict)
        return get_json_result(data=_build_session_response(conv_dict))
    except Exception as ex:
        return server_error_response(ex)
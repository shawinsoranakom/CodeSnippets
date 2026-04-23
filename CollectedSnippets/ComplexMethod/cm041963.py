async def plan(role: "STRole", roles: dict["STRole"], new_day: bool, retrieved: dict) -> str:
    # PART 1: Generate the hourly schedule.
    if new_day:
        await _long_term_planning(role, new_day)

    # PART 2: If the current action has expired, we want to create a new plan.
    act_check_finished = role.scratch.act_check_finished()
    logger.info(f"Role: {role.name} act_check_finished is {act_check_finished}")
    if act_check_finished:
        await _determine_action(role)

    # PART 3: If you perceived an event that needs to be responded to (saw
    # another role), and retrieved relevant information.
    # Step 1: Retrieved may have multiple events represented in it. The first
    #         job here is to determine which of the events we want to focus
    #         on for the role.
    #         <focused_event> takes the form of a dictionary like this:
    #         dictionary {["curr_event"] = <ConceptNode>,
    #                     ["events"] = [<ConceptNode>, ...],
    #                     ["thoughts"] = [<ConceptNode>, ...]}
    focused_event = False
    if retrieved.keys():
        focused_event = _choose_retrieved(role.name, retrieved)

    # Step 2: Once we choose an event, we need to determine whether the
    #         role will take any actions for the perceived event. There are
    #         three possible modes of reaction returned by _should_react.
    #         a) "chat with {target_role.name}"
    #         b) "react"
    #         c) False
    logger.info(f"Role: {role.name} focused_event: {focused_event}")
    if focused_event:
        reaction_mode = await _should_react(role, focused_event, roles)
        logger.info(f"Role: {role.name} reaction_mode: {reaction_mode}")
        if reaction_mode:
            # If we do want to chat, then we generate conversation
            if reaction_mode[:9] == "chat with":
                await _chat_react(role, reaction_mode, roles)
            elif reaction_mode[:4] == "wait":
                await _wait_react(role, reaction_mode)

    # Step 3: Chat-related state clean up.
    # If the persona is not chatting with anyone, we clean up any of the
    # chat-related states here.
    if role.rc.scratch.act_event[1] != "chat with":
        role.rc.scratch.chatting_with = None
        role.rc.scratch.chat = None
        role.rc.scratch.chatting_end_time = None
    # We want to make sure that the persona does not keep conversing with each
    # other in an infinite loop. So, chatting_with_buffer maintains a form of
    # buffer that makes the persona wait from talking to the same target
    # immediately after chatting once. We keep track of the buffer value here.
    curr_persona_chat_buffer = role.rc.scratch.chatting_with_buffer
    for persona_name, buffer_count in curr_persona_chat_buffer.items():
        if persona_name != role.rc.scratch.chatting_with:
            role.rc.scratch.chatting_with_buffer[persona_name] -= 1

    return role.rc.scratch.act_address
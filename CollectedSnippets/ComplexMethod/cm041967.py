async def _determine_action(role: "STRole"):
    """
    Creates the next action sequence for the role.
    The main goal of this function is to run "add_new_action" on the role's
    scratch space, which sets up all the action related variables for the next
    action.
    As a part of this, the role may need to decompose its hourly schedule as
    needed.
    INPUT
        role: Current <Persona> instance whose action we are determining.
    """

    def determine_decomp(act_desp, act_dura):
        """
        Given an action description and its duration, we determine whether we need
        to decompose it. If the action is about the agent sleeping, we generally
        do not want to decompose it, so that's what we catch here.

        INPUT:
        act_desp: the description of the action (e.g., "sleeping")
        act_dura: the duration of the action in minutes.
        OUTPUT:
        a boolean. True if we need to decompose, False otherwise.
        """
        if "sleep" not in act_desp and "bed" not in act_desp:
            return True
        elif "sleeping" in act_desp or "asleep" in act_desp or "in bed" in act_desp:
            return False
        elif "sleep" in act_desp or "bed" in act_desp:
            if act_dura > 60:
                return False
        return True

    # The goal of this function is to get us the action associated with
    # <curr_index>. As a part of this, we may need to decompose some large
    # chunk actions.
    # Importantly, we try to decompose at least two hours worth of schedule at
    # any given point.
    curr_index = role.scratch.get_f_daily_schedule_index()
    curr_index_60 = role.scratch.get_f_daily_schedule_index(advance=60)

    logger.info(f"f_daily_schedule: {role.scratch.f_daily_schedule}")
    # * Decompose *
    # During the first hour of the day, we need to decompose two hours
    # sequence. We do that here.
    if curr_index == 0:
        # This portion is invoked if it is the first hour of the day.
        act_desp, act_dura = role.scratch.f_daily_schedule[curr_index]
        if act_dura >= 60:
            # We decompose if the next action is longer than an hour, and fits the
            # criteria described in determine_decomp.
            if determine_decomp(act_desp, act_dura):
                role.scratch.f_daily_schedule[curr_index : curr_index + 1] = await TaskDecomp().run(
                    role, act_desp, act_dura
                )
        if curr_index_60 + 1 < len(role.scratch.f_daily_schedule):
            act_desp, act_dura = role.scratch.f_daily_schedule[curr_index_60 + 1]
            if act_dura >= 60:
                if determine_decomp(act_desp, act_dura):
                    role.scratch.f_daily_schedule[curr_index_60 + 1 : curr_index_60 + 2] = await TaskDecomp().run(
                        role, act_desp, act_dura
                    )

    if curr_index_60 < len(role.scratch.f_daily_schedule):
        # If it is not the first hour of the day, this is always invoked (it is
        # also invoked during the first hour of the day -- to double up so we can
        # decompose two hours in one go). Of course, we need to have something to
        # decompose as well, so we check for that too.
        if role.scratch.curr_time.hour < 23:
            # And we don't want to decompose after 11 pm.
            act_desp, act_dura = role.scratch.f_daily_schedule[curr_index_60]
            if act_dura >= 60:
                if determine_decomp(act_desp, act_dura):
                    role.scratch.f_daily_schedule[curr_index_60 : curr_index_60 + 1] = await TaskDecomp().run(
                        role, act_desp, act_dura
                    )
    # * End of Decompose *

    # Generate an <Action> instance from the action description and duration. By
    # this point, we assume that all the relevant actions are decomposed and
    # ready in f_daily_schedule.
    logger.debug("DEBUG LJSDLFSKJF")
    for i in role.scratch.f_daily_schedule:
        logger.debug(i)
    logger.debug(curr_index)
    logger.debug(len(role.scratch.f_daily_schedule))
    logger.debug(role.scratch.name)

    # 1440
    x_emergency = 0
    for i in role.scratch.f_daily_schedule:
        x_emergency += i[1]

    if 1440 - x_emergency > 0:
        logger.info(f"x_emergency__AAA: {x_emergency}")
    role.scratch.f_daily_schedule += [["sleeping", 1440 - x_emergency]]

    act_desp, act_dura = role.scratch.f_daily_schedule[curr_index]

    new_action_details = await GenActionDetails().run(role, act_desp, act_dura)
    # Adding the action to role's queue.
    role.scratch.add_new_action(**new_action_details)
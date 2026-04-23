async def generate_new_decomp_schedule(
    role: "STRole", inserted_act: str, inserted_act_dur: int, start_hour: int, end_hour: int
):
    # Step 1: Setting up the core variables for the function.
    # <p> is the role whose schedule we are editing right now.
    scratch = role.rc.scratch
    # <today_min_pass> indicates the number of minutes that have passed today.
    today_min_pass = int(scratch.curr_time.hour) * 60 + int(scratch.curr_time.minute) + 1

    # Step 2: We need to create <main_act_dur> and <truncated_act_dur>.
    main_act_dur = []
    truncated_act_dur = []
    dur_sum = 0  # duration sum
    count = 0  # enumerate count
    truncated_fin = False

    logger.debug(f"DEBUG::: {scratch.name}")
    for act, dur in scratch.f_daily_schedule:
        if (dur_sum >= start_hour * 60) and (dur_sum < end_hour * 60):
            main_act_dur += [[act, dur]]
            if dur_sum <= today_min_pass:
                truncated_act_dur += [[act, dur]]
            elif dur_sum > today_min_pass and not truncated_fin:
                # We need to insert that last act, duration list like this one:
                # e.g., ['wakes up and completes her morning routine (wakes up...)', 2]
                truncated_act_dur += [[scratch.f_daily_schedule[count][0], dur_sum - today_min_pass]]
                truncated_act_dur[-1][-1] -= (
                    dur_sum - today_min_pass
                )  # DEC 7 DEBUG;.. is the +1 the right thing to do???
                # DEC 7 DEBUG;.. is the +1 the right thing to do???
                # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass + 1)
                logger.debug(f"DEBUG::: {truncated_act_dur}")

                # DEC 7 DEBUG;.. is the +1 the right thing to do???
                # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass)
                truncated_fin = True
        dur_sum += dur
        count += 1

    main_act_dur = main_act_dur

    x = (
        truncated_act_dur[-1][0].split("(")[0].strip()
        + " (on the way to "
        + truncated_act_dur[-1][0].split("(")[-1][:-1]
        + ")"
    )
    truncated_act_dur[-1][0] = x

    if "(" in truncated_act_dur[-1][0]:
        inserted_act = truncated_act_dur[-1][0].split("(")[0].strip() + " (" + inserted_act + ")"

    # To do inserted_act_dur+1 below is an important decision but I'm not sure
    # if I understand the full extent of its implications. Might want to
    # revisit.
    truncated_act_dur += [[inserted_act, inserted_act_dur]]
    start_time_hour = datetime.datetime(2022, 10, 31, 0, 0) + datetime.timedelta(hours=start_hour)
    end_time_hour = datetime.datetime(2022, 10, 31, 0, 0) + datetime.timedelta(hours=end_hour)

    return await NewDecompSchedule().run(
        role, main_act_dur, truncated_act_dur, start_time_hour, end_time_hour, inserted_act, inserted_act_dur
    )
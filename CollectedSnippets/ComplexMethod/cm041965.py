async def _create_react(
    role: "STRole",
    inserted_act: str,
    inserted_act_dur: int,
    act_address: str,
    act_event: Tuple,
    chatting_with: str,
    chat: list,
    chatting_with_buffer: dict,
    chatting_end_time: datetime,
    act_pronunciatio: str,
    act_obj_description: str,
    act_obj_pronunciatio: str,
    act_obj_event: Tuple,
    act_start_time=None,
):
    p = role
    scratch = role.rc.scratch

    min_sum = 0
    for i in range(scratch.get_f_daily_schedule_hourly_org_index()):
        min_sum += scratch.f_daily_schedule_hourly_org[i][1]
    start_hour = int(min_sum / 60)

    if scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1] >= 120:
        end_hour = (
            start_hour + scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1] / 60
        )

    elif (
        scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1]
        + scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index() + 1][1]
    ):
        end_hour = start_hour + (
            (
                scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index()][1]
                + scratch.f_daily_schedule_hourly_org[scratch.get_f_daily_schedule_hourly_org_index() + 1][1]
            )
            / 60
        )

    else:
        end_hour = start_hour + 2
    end_hour = int(end_hour)

    dur_sum = 0
    count = 0
    start_index = None
    end_index = None
    for act, dur in scratch.f_daily_schedule:
        if dur_sum >= start_hour * 60 and start_index is None:
            start_index = count
        if dur_sum >= end_hour * 60 and end_index is None:
            end_index = count
        dur_sum += dur
        count += 1

    ret = await generate_new_decomp_schedule(p, inserted_act, inserted_act_dur, start_hour, end_hour)
    scratch.f_daily_schedule[start_index:end_index] = ret
    scratch.add_new_action(
        act_address,
        inserted_act_dur,
        inserted_act,
        act_pronunciatio,
        act_event,
        chatting_with,
        chat,
        chatting_with_buffer,
        chatting_end_time,
        act_obj_description,
        act_obj_pronunciatio,
        act_obj_event,
        act_start_time,
    )
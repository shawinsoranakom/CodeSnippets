async def lets_react(init_role: "STRole", target_role: "STRole", retrieved: dict):
        if init_role.name == target_role.name:
            logger.info(f"Role: {role.name} _should_react lets_react meet same role, return False")
            return False

        scratch = init_role.rc.scratch
        target_scratch = target_role.rc.scratch
        if (
            not target_scratch.act_address
            or not target_scratch.act_description
            or not scratch.act_address
            or not scratch.act_description
        ):
            return False

        if "sleeping" in target_scratch.act_description or "sleeping" in scratch.act_description:
            return False

        # return False
        if scratch.curr_time.hour == 23:
            return False

        if "waiting" in target_scratch.act_description:
            return False
        if scratch.planned_path == []:
            return False

        if scratch.act_address != target_scratch.act_address:
            return False

        react_mode = await DecideToTalk().run(init_role, target_role, retrieved)

        if react_mode == "1":
            wait_until = (
                target_scratch.act_start_time + datetime.timedelta(minutes=target_scratch.act_duration - 1)
            ).strftime("%B %d, %Y, %H:%M:%S")
            return f"wait: {wait_until}"
        elif react_mode == "2":
            return False
            return "do other things"
        else:
            return False
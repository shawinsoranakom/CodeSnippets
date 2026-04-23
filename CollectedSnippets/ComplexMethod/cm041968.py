async def lets_talk(init_role: "STRole", target_role: "STRole", retrieved: dict):
        if init_role.name == target_role.name:
            logger.info(f"Role: {role.name} _should_react lets_talk meet same role, return False")
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

        if scratch.curr_time.hour == 23:
            return False

        if "<waiting>" in target_scratch.act_address:
            return False

        if target_scratch.chatting_with or scratch.chatting_with:
            return False

        if target_role.name in scratch.chatting_with_buffer:
            if scratch.chatting_with_buffer[target_role.name] > 0:
                return False

        if await DecideToTalk().run(init_role, target_role, retrieved):
            return True

        return False
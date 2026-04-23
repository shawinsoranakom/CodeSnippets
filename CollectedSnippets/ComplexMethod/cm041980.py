def create_prompt_input(
            access_tile: dict[str, str],
            init_role: "STRole",
            target_role: "STRole",
            retrieved: dict,
            curr_context: str,
            curr_chat: list[str],
        ):
            role = init_role
            scratch = role.rc.scratch
            target_scratch = target_role.rc.scratch
            prev_convo_insert = "\n"
            if role.rc.memory.chat_list:
                for i in role.rc.memory.chat_list:
                    if i.object == target_role.name:
                        v1 = int((scratch.curr_time - i.created).total_seconds() / 60)
                        prev_convo_insert += (
                            f"{str(v1)} minutes ago, {scratch.name} and "
                            f"{target_scratch.name} were already {i.description} "
                            f"This context takes place after that conversation."
                        )
                        break
            if prev_convo_insert == "\n":
                prev_convo_insert = ""
            if role.rc.memory.chat_list:
                if int((scratch.curr_time - role.rc.memory.chat_list[-1].created).total_seconds() / 60) > 480:
                    prev_convo_insert = ""
            logger.info(f"prev_convo_insert: {prev_convo_insert}")

            curr_sector = f"{access_tile['sector']}"
            curr_arena = f"{access_tile['arena']}"
            curr_location = f"{curr_arena} in {curr_sector}"

            retrieved_str = ""
            for key, vals in retrieved.items():
                for v in vals:
                    retrieved_str += f"- {v.description}\n"

            convo_str = ""
            for i in curr_chat:
                convo_str += ": ".join(i) + "\n"
            if convo_str == "":
                convo_str = "[The conversation has not started yet -- start it!]"

            init_iss = f"Here is Here is a brief description of {scratch.name}.\n{scratch.get_str_iss()}"
            prompt_input = [
                init_iss,
                scratch.name,
                retrieved_str,
                prev_convo_insert,
                curr_location,
                curr_context,
                scratch.name,
                target_scratch.name,
                convo_str,
                scratch.name,
                target_scratch.name,
                scratch.name,
                scratch.name,
                scratch.name,
            ]
            return prompt_input
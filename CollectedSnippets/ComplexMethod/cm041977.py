def create_prompt_input(init_role: "STRole", target_role: "STRole", retrieved: dict) -> str:
            scratch = init_role.rc.scratch
            target_scratch = target_role.rc.scratch
            last_chat = init_role.rc.memory.get_last_chat(target_role.name)
            last_chatted_time = ""
            last_chat_about = ""
            if last_chat:
                last_chatted_time = last_chat.created.strftime("%B %d, %Y, %H:%M:%S")
                last_chat_about = last_chat.description

            context = ""
            for c_node in retrieved["events"]:
                curr_desc = c_node.description.split(" ")
                curr_desc[2:3] = ["was"]
                curr_desc = " ".join(curr_desc)
                context += f"{curr_desc}. "
            context += "\n"
            for c_node in retrieved["thoughts"]:
                context += f"{c_node.description}. "

            curr_time = scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
            init_act_desc = scratch.act_description
            if "(" in init_act_desc:
                init_act_desc = init_act_desc.split("(")[-1][:-1]

            if len(scratch.planned_path) == 0 and "waiting" not in init_act_desc:
                init_p_desc = f"{init_role.name} is already {init_act_desc}"
            elif "waiting" in init_act_desc:
                init_p_desc = f"{init_role.name} is {init_act_desc}"
            else:
                init_p_desc = f"{init_role.name} is on the way to {init_act_desc}"

            target_act_desc = scratch.act_description
            if "(" in target_act_desc:
                target_act_desc = target_act_desc.split("(")[-1][:-1]

            if len(target_scratch.planned_path) == 0 and "waiting" not in init_act_desc:
                target_p_desc = f"{target_role.name} is already {target_act_desc}"
            elif "waiting" in init_act_desc:
                target_p_desc = f"{init_role.name} is {init_act_desc}"
            else:
                target_p_desc = f"{target_role.name} is on the way to {target_act_desc}"

            prompt_input = []
            prompt_input += [context]

            prompt_input += [curr_time]

            prompt_input += [init_role.name]
            prompt_input += [target_role.name]
            prompt_input += [last_chatted_time]
            prompt_input += [last_chat_about]

            prompt_input += [init_p_desc]
            prompt_input += [target_p_desc]
            prompt_input += [init_role.name]
            prompt_input += [target_role.name]
            return prompt_input
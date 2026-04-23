def generate_message_payload(inputs, llm_kwargs, history, system_prompt):
    conversation_cnt = len(history) // 2
    if system_prompt == "": system_prompt = "Hello"
    messages = [{"role": "user", "content": system_prompt}]
    messages.append({"role": "assistant", "content": 'Certainly!'})
    if conversation_cnt:
        for index in range(0, 2*conversation_cnt, 2):
            what_i_have_asked = {}
            what_i_have_asked["role"] = "user"
            what_i_have_asked["content"] = history[index] if history[index]!="" else "Hello"
            what_gpt_answer = {}
            what_gpt_answer["role"] = "assistant"
            what_gpt_answer["content"] = history[index+1] if history[index]!="" else "Hello"
            if what_i_have_asked["content"] != "":
                if what_gpt_answer["content"] == "": continue
                if what_gpt_answer["content"] == timeout_bot_msg: continue
                messages.append(what_i_have_asked)
                messages.append(what_gpt_answer)
            else:
                messages[-1]['content'] = what_gpt_answer['content']
    what_i_ask_now = {}
    what_i_ask_now["role"] = "user"
    what_i_ask_now["content"] = inputs
    messages.append(what_i_ask_now)
    return messages
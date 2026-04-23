def trans_json(word_to_translate, language, special=False):
    if len(word_to_translate) == 0: return {}
    from crazy_functions.crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency
    from toolbox import get_conf, ChatBotWithCookies, load_chat_cookies

    cookies = load_chat_cookies()
    llm_kwargs = {
        'api_key': cookies['api_key'],
        'llm_model': cookies['llm_model'],
        'top_p':1.0,
        'max_length': None,
        'temperature':0.4,
    }
    import random
    N_EACH_REQ = random.randint(16, 32)
    random.shuffle(word_to_translate)
    word_to_translate_split = split_list(word_to_translate, N_EACH_REQ)
    inputs_array = [{k:"#" for k in s} for s in word_to_translate_split]
    inputs_array = [ json.dumps(i, ensure_ascii=False)  for i in inputs_array]

    inputs_show_user_array = inputs_array
    history_array = [[] for _ in inputs_array]
    sys_prompt_array = [TransPrompt for _ in inputs_array]
    chatbot = ChatBotWithCookies(llm_kwargs)
    gpt_say_generator = request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array,
        inputs_show_user_array,
        llm_kwargs,
        chatbot,
        history_array,
        sys_prompt_array,
    )
    while True:
        try:
            gpt_say = next(gpt_say_generator)
            print(gpt_say[1][0][1])
        except StopIteration as e:
            result = e.value
            break
    translated_result = {}
    for i, r in enumerate(result):
        if i%2 == 1:
            try:
                translated_result.update(json.loads(result[i]))
            except:
                print(result[i])
    print(result)
    return translated_result
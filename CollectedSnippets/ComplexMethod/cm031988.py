def trans(word_to_translate, language, special=False):
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
    word_to_translate_split = split_list(word_to_translate, N_EACH_REQ)
    inputs_array = [str(s) for s in word_to_translate_split]
    inputs_show_user_array = inputs_array
    history_array = [[] for _ in inputs_array]
    if special: #  to English using CamelCase Naming Convention
        sys_prompt_array = [f"Translate following names to English with CamelCase naming convention. Keep original format" for _ in inputs_array]
    else:
        sys_prompt_array = [f"Translate following sentences to {LANG}. E.g., You should translate sentences to the following format ['translation of sentence 1', 'translation of sentence 2']. Do NOT answer with Chinese!" for _ in inputs_array]
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
                res_before_trans = eval(result[i-1])
                res_after_trans = eval(result[i])
                if len(res_before_trans) != len(res_after_trans):
                    raise RuntimeError
                for a,b in zip(res_before_trans, res_after_trans):
                    translated_result[a] = b
            except:
                # try:
                    # res_before_trans = word_to_translate_split[(i-1)//2]
                    # res_after_trans = [s for s in result[i].split("', '")]
                #     for a,b in zip(res_before_trans, res_after_trans):
                #         translated_result[a] = b
                # except:
                print('GPT answers with unexpected format, some words may not be translated, but you can try again later to increase translation coverage.')
                res_before_trans = eval(result[i-1])
                for a in res_before_trans:
                    translated_result[a] = None
    return translated_result
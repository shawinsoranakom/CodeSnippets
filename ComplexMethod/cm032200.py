def select_api_key(keys, llm_model):
    import random
    avail_key_list = []
    key_list = keys.split(',')

    if llm_model.startswith('gpt-') or llm_model.startswith('chatgpt-') or \
       llm_model.startswith('one-api-') or is_o_family_for_openai(llm_model):
        for k in key_list:
            if is_openai_api_key(k): avail_key_list.append(k)

    if llm_model.startswith('api2d-'):
        for k in key_list:
            if is_api2d_key(k): avail_key_list.append(k)

    if llm_model.startswith('azure-'):
        for k in key_list:
            if is_azure_api_key(k): avail_key_list.append(k)

    if llm_model.startswith('cohere-'):
        for k in key_list:
            if is_cohere_api_key(k): avail_key_list.append(k)

    if llm_model.startswith('openrouter-'):
        for k in key_list:
            if is_openroute_api_key(k): avail_key_list.append(k)

    if len(avail_key_list) == 0:
        raise RuntimeError(f"您提供的api-key不满足要求，不包含任何可用于{llm_model}的api-key。您可能选择了错误的模型或请求源（左上角更换模型菜单中可切换openai,azure,claude,cohere等请求源）。")

    api_key = random.choice(avail_key_list) # 随机负载均衡
    return api_key
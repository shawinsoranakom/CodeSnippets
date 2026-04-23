def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream = True, additional_fn=None):
    """
    发送至chatGPT，流式获取输出。
    用于基础的对话功能。
    inputs 是本次问询的输入
    top_p, temperature是chatGPT的内部调优参数
    history 是之前的对话列表（注意无论是inputs还是history，内容太长了都会触发token数量溢出的错误）
    chatbot 为WebUI中显示的对话列表，修改它，然后yield出去，可以直接修改对话界面内容
    additional_fn代表点击的哪个按钮，按钮见functional.py
    """
    if inputs == "":     inputs = "空空如也的输入栏"
    if len(ANTHROPIC_API_KEY) == 0:
        chatbot.append((inputs, "没有设置ANTHROPIC_API_KEY"))
        yield from update_ui(chatbot=chatbot, history=history, msg="等待响应") # 刷新界面
        return

    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    have_recent_file, image_paths = every_image_file_in_path(chatbot)
    if len(image_paths) > 20:
        chatbot.append((inputs, "图片数量超过api上限(20张)"))
        yield from update_ui(chatbot=chatbot, history=history, msg="等待响应")
        return

    if any([llm_kwargs['llm_model'] == model for model in Claude_3_Models]) and have_recent_file:
        if inputs == "" or inputs == "空空如也的输入栏":     inputs = "请描述给出的图片"
        system_prompt += picture_system_prompt  # 由于没有单独的参数保存包含图片的历史，所以只能通过提示词对第几张图片进行定位
        chatbot.append((make_media_input(history,inputs, image_paths), ""))
        yield from update_ui(chatbot=chatbot, history=history, msg="等待响应") # 刷新界面
    else:
        chatbot.append((inputs, ""))
        yield from update_ui(chatbot=chatbot, history=history, msg="等待响应") # 刷新界面

    try:
        headers, message = generate_payload(inputs, llm_kwargs, history, system_prompt, image_paths)
    except RuntimeError as e:
        chatbot[-1] = (inputs, f"您提供的api-key不满足要求，不包含任何可用于{llm_kwargs['llm_model']}的api-key。您可能选择了错误的模型或请求源。")
        yield from update_ui(chatbot=chatbot, history=history, msg="api-key不满足要求") # 刷新界面
        return

    history.append(inputs); history.append("")

    retry = 0
    while True:
        try:
            # make a POST request to the API endpoint, stream=True
            from .bridge_all import model_info
            endpoint = model_info[llm_kwargs['llm_model']]['endpoint']
            response = requests.post(endpoint, headers=headers, json=message,
                                     proxies=proxies, stream=True, timeout=TIMEOUT_SECONDS);break
        except requests.exceptions.ReadTimeout as e:
            retry += 1
            traceback.print_exc()
            if retry > MAX_RETRY: raise TimeoutError
            if MAX_RETRY!=0: logger.error(f'请求超时，正在重试 ({retry}/{MAX_RETRY}) ……')
    stream_response = response.iter_lines()
    gpt_replying_buffer = ""

    while True:
        try: chunk = next(stream_response)
        except StopIteration:
            break
        except requests.exceptions.ConnectionError:
            chunk = next(stream_response) # 失败了，重试一次？再失败就没办法了。
        need_to_pass, chunkjson, is_last_chunk = decode_chunk(chunk)
        if chunk:
            try:
                if need_to_pass:
                    pass
                elif is_last_chunk:
                    log_chat(llm_model=llm_kwargs["llm_model"], input_str=inputs, output_str=gpt_replying_buffer)
                    # logger.info(f'[response] {gpt_replying_buffer}')
                    break
                else:
                    if chunkjson and chunkjson['type'] == 'content_block_delta':
                        gpt_replying_buffer += chunkjson['delta']['text']
                        history[-1] = gpt_replying_buffer
                        chatbot[-1] = (history[-2], history[-1])
                        yield from update_ui(chatbot=chatbot, history=history, msg='正常') # 刷新界面

            except Exception as e:
                chunk = get_full_error(chunk, stream_response)
                chunk_decoded = chunk.decode()
                error_msg = chunk_decoded
                logger.error(error_msg)
                raise RuntimeError("Json解析不合常规")
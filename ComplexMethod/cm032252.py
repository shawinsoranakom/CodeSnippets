def predict(inputs:str, llm_kwargs:dict, plugin_kwargs:dict, chatbot:ChatBotWithCookies,
            history:list=[], system_prompt:str='', stream:bool=True, additional_fn:str=None):
    """
    发送至chatGPT，流式获取输出。
    用于基础的对话功能。
    inputs 是本次问询的输入
    top_p, temperature是chatGPT的内部调优参数
    history 是之前的对话列表（注意无论是inputs还是history，内容太长了都会触发token数量溢出的错误）
    chatbot 为WebUI中显示的对话列表，修改它，然后yield出去，可以直接修改对话界面内容
    additional_fn代表点击的哪个按钮，按钮见functional.py
    """
    from request_llms.bridge_all import model_info
    if is_any_api_key(inputs):
        chatbot._cookies['api_key'] = inputs
        chatbot.append(("输入已识别为openai的api_key", what_keys(inputs)))
        yield from update_ui(chatbot=chatbot, history=history, msg="api_key已导入") # 刷新界面
        return
    elif not is_any_api_key(chatbot._cookies['api_key']):
        chatbot.append((inputs, "缺少api_key。\n\n1. 临时解决方案：直接在输入区键入api_key，然后回车提交。\n\n2. 长效解决方案：在config.py中配置。"))
        yield from update_ui(chatbot=chatbot, history=history, msg="缺少api_key") # 刷新界面
        return

    user_input = inputs
    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    # 多模态模型
    has_multimodal_capacity = model_info[llm_kwargs['llm_model']].get('has_multimodal_capacity', False)
    if has_multimodal_capacity:
        has_recent_image_upload, image_paths = have_any_recent_upload_image_files(chatbot, pop=True)
    else:
        has_recent_image_upload, image_paths = False, []
    if has_recent_image_upload:
        _inputs, image_base64_array = make_multimodal_input(inputs, image_paths)
    else:
        _inputs, image_base64_array = inputs, []
    chatbot.append((_inputs, ""))
    yield from update_ui(chatbot=chatbot, history=history, msg="等待响应") # 刷新界面

    # 禁用stream的特殊模型处理
    if model_info[llm_kwargs['llm_model']].get('openai_disable_stream', False): stream = False
    else: stream = True

    # check mis-behavior
    if is_the_upload_folder(user_input):
        chatbot[-1] = (inputs, f"[Local Message] 检测到操作错误！当您上传文档之后，需点击“**函数插件区**”按钮进行处理，请勿点击“提交”按钮或者“基础功能区”按钮。")
        yield from update_ui(chatbot=chatbot, history=history, msg="正常") # 刷新界面
        time.sleep(2)

    try:
        headers, payload = generate_payload(inputs, llm_kwargs, history, system_prompt, image_base64_array, has_multimodal_capacity, stream)
    except RuntimeError as e:
        chatbot[-1] = (inputs, f"您提供的api-key不满足要求，不包含任何可用于{llm_kwargs['llm_model']}的api-key。您可能选择了错误的模型或请求源。")
        yield from update_ui(chatbot=chatbot, history=history, msg="api-key不满足要求") # 刷新界面
        return

    # 检查endpoint是否合法
    try:
        endpoint = verify_endpoint(model_info[llm_kwargs['llm_model']]['endpoint'])
    except:
        tb_str = '```\n' + trimmed_format_exc() + '```'
        chatbot[-1] = (inputs, tb_str)
        yield from update_ui(chatbot=chatbot, history=history, msg="Endpoint不满足要求") # 刷新界面
        return

    # 加入历史
    if has_recent_image_upload:
        history.extend([_inputs, ""])
    else:
        history.extend([inputs, ""])

    retry = 0
    previous_ui_reflesh_time = 0
    ui_reflesh_min_interval = 0.0
    while True:
        try:
            # make a POST request to the API endpoint, stream=True
            response = requests.post(endpoint, headers=headers, proxies=proxies,
                                    json=payload, stream=stream, timeout=TIMEOUT_SECONDS);break
        except:
            retry += 1
            chatbot[-1] = ((chatbot[-1][0], timeout_bot_msg))
            retry_msg = f"，正在重试 ({retry}/{MAX_RETRY}) ……" if MAX_RETRY > 0 else ""
            yield from update_ui(chatbot=chatbot, history=history, msg="请求超时"+retry_msg) # 刷新界面
            if retry > MAX_RETRY: raise TimeoutError

    if not stream:
        # 该分支仅适用于不支持stream的o1模型，其他情形一律不适用
        yield from handle_o1_model_special(response, inputs, llm_kwargs, chatbot, history)
        return

    if stream:
        reach_termination = False   # 处理一些 new-api 的奇葩异常
        gpt_replying_buffer = ""
        is_head_of_the_stream = True
        stream_response =  response.iter_lines()
        while True:
            try:
                chunk = next(stream_response)
            except StopIteration:
                # 非OpenAI官方接口的出现这样的报错，OpenAI和API2D不会走这里
                chunk_decoded = chunk.decode()
                error_msg = chunk_decoded
                # 首先排除一个one-api没有done数据包的第三方Bug情形
                if len(gpt_replying_buffer.strip()) > 0 and len(error_msg) == 0:
                    yield from update_ui(chatbot=chatbot, history=history, msg="检测到有缺陷的接口，建议选择更稳定的接口。")
                    if not reach_termination:
                        reach_termination = True
                        log_chat(llm_model=llm_kwargs["llm_model"], input_str=inputs, output_str=gpt_replying_buffer)
                    break
                # 其他情况，直接返回报错
                chatbot, history = handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg)
                yield from update_ui(chatbot=chatbot, history=history, msg="接口返回了错误:" + chunk.decode()) # 刷新界面
                return

            # 提前读取一些信息 （用于判断异常）
            chunk_decoded, chunkjson, has_choices, choice_valid, has_content, has_role = decode_chunk(chunk)

            if is_head_of_the_stream and (r'"object":"error"' not in chunk_decoded) and (r"content" not in chunk_decoded):
                # 数据流的第一帧不携带content
                is_head_of_the_stream = False; continue

            if "error" in chunk_decoded: logger.error(f"接口返回了未知错误: {chunk_decoded}")

            if chunk:
                try:
                    if has_choices and not choice_valid:
                        # 一些垃圾第三方接口的出现这样的错误
                        continue
                    if ('data: [DONE]' not in chunk_decoded) and len(chunk_decoded) > 0 and (chunkjson is None):
                        # 传递进来一些奇怪的东西
                        raise ValueError(f'无法读取以下数据，请检查配置。\n\n{chunk_decoded}')
                    # 前者是API2D & One-API的结束条件，后者是OPENAI的结束条件
                    one_api_terminate = ('data: [DONE]' in chunk_decoded)
                    openai_terminate = (has_choices) and (len(chunkjson['choices'][0]["delta"]) == 0)
                    if one_api_terminate or openai_terminate:
                        is_termination_certain = False
                        if one_api_terminate: is_termination_certain = True # 抓取符合规范的结束条件
                        elif (has_choices) and (chunkjson['choices'][0].get('finish_reason', 'null') == 'stop'): is_termination_certain = True # 抓取符合规范的结束条件
                        if is_termination_certain:
                            reach_termination = True
                            log_chat(llm_model=llm_kwargs["llm_model"], input_str=inputs, output_str=gpt_replying_buffer)
                            break # 对于符合规范的接口，这里可以break
                        else:
                            continue # 对于不符合规范的接口，这里需要继续
                    # 到这里，我们已经可以假定必须包含choice了
                    try:
                        status_text = f"finish_reason: {chunkjson['choices'][0].get('finish_reason', 'null')}"
                    except:
                        logger.error(f"一些第三方接口出现这样的错误，兼容一下吧: {chunk_decoded}")
                    # 处理数据流的主体
                    if has_content:
                        # 正常情况
                        gpt_replying_buffer = gpt_replying_buffer + chunkjson['choices'][0]["delta"]["content"]
                    elif has_role:
                        # 一些第三方接口的出现这样的错误，兼容一下吧
                        continue
                    else:
                        # 至此已经超出了正常接口应该进入的范围，一些第三方接口会出现这样的错误
                        if chunkjson['choices'][0]["delta"].get("content", None) is None:
                            logger.error(f"一些第三方接口出现这样的错误，兼容一下吧: {chunk_decoded}")
                            continue
                        gpt_replying_buffer = gpt_replying_buffer + chunkjson['choices'][0]["delta"]["content"]

                    history[-1] = gpt_replying_buffer
                    chatbot[-1] = (history[-2], history[-1])
                    if time.time() - previous_ui_reflesh_time > ui_reflesh_min_interval:
                        yield from update_ui(chatbot=chatbot, history=history, msg=status_text) # 刷新界面
                        previous_ui_reflesh_time = time.time()
                except Exception as e:
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json解析不合常规") # 刷新界面
                    chunk = get_full_error(chunk, stream_response)
                    chunk_decoded = chunk.decode()
                    error_msg = chunk_decoded
                    chatbot, history = handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg)
                    logger.error(error_msg)
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json解析异常" + error_msg) # 刷新界面
                    return
        yield from update_ui(chatbot=chatbot, history=history, msg="完成") # 刷新界面
        return
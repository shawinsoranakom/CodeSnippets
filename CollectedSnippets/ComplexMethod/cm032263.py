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
    user_input = inputs
    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    raw_input = inputs
    logger.info(f'[raw_input] {raw_input}')
    chatbot.append((inputs, ""))
    yield from update_ui(chatbot=chatbot, history=history, msg="等待响应") # 刷新界面

    # check mis-behavior
    if is_the_upload_folder(user_input):
        chatbot[-1] = (inputs, f"[Local Message] 检测到操作错误！当您上传文档之后，需点击“**函数插件区**”按钮进行处理，请勿点击“提交”按钮或者“基础功能区”按钮。")
        yield from update_ui(chatbot=chatbot, history=history, msg="正常") # 刷新界面
        time.sleep(2)

    headers, payload = generate_payload(inputs, llm_kwargs, history, system_prompt, stream)

    from .bridge_all import model_info
    endpoint = model_info[llm_kwargs['llm_model']]['endpoint']

    history.append(inputs); history.append("")

    retry = 0
    if proxies is not None:
        logger.error("Ollama不会使用代理服务器, 忽略了proxies的设置。")
    while True:
        try:
            # make a POST request to the API endpoint, stream=True
            response = requests.post(endpoint, headers=headers, proxies=None,
                                    json=payload, stream=True, timeout=TIMEOUT_SECONDS);break
        except:
            retry += 1
            chatbot[-1] = ((chatbot[-1][0], timeout_bot_msg))
            retry_msg = f"，正在重试 ({retry}/{MAX_RETRY}) ……" if MAX_RETRY > 0 else ""
            yield from update_ui(chatbot=chatbot, history=history, msg="请求超时"+retry_msg) # 刷新界面
            if retry > MAX_RETRY: raise TimeoutError

    gpt_replying_buffer = ""

    if stream:
        stream_response =  response.iter_lines()
        while True:
            try:
                chunk = next(stream_response)
            except StopIteration:
                break
            except requests.exceptions.ConnectionError:
                chunk = next(stream_response) # 失败了，重试一次？再失败就没办法了。

            # 提前读取一些信息 （用于判断异常）
            chunk_decoded, chunkjson, is_last_chunk = decode_chunk(chunk)

            if chunk:
                try:
                    if is_last_chunk:
                        # 判定为数据流的结束，gpt_replying_buffer也写完了
                        logger.info(f'[response] {gpt_replying_buffer}')
                        break
                    # 处理数据流的主体
                    try:
                        status_text = f"finish_reason: {chunkjson['error'].get('message', 'null')}"
                    except:
                        status_text = "finish_reason: null"
                    gpt_replying_buffer = gpt_replying_buffer + chunkjson['message']["content"]
                    # 如果这里抛出异常，一般是文本过长，详情见get_full_error的输出
                    history[-1] = gpt_replying_buffer
                    chatbot[-1] = (history[-2], history[-1])
                    yield from update_ui(chatbot=chatbot, history=history, msg=status_text) # 刷新界面
                except Exception as e:
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json解析不合常规") # 刷新界面
                    chunk = get_full_error(chunk, stream_response)
                    chunk_decoded = chunk.decode()
                    error_msg = chunk_decoded
                    chatbot, history = handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg)
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json异常" + error_msg) # 刷新界面
                    logger.error(error_msg)
                    return
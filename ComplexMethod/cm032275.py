def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream = True, additional_fn=None):

    have_recent_file, image_paths = have_any_recent_upload_image_files(chatbot)

    if is_any_api_key(inputs):
        chatbot._cookies['api_key'] = inputs
        chatbot.append(("输入已识别为openai的api_key", what_keys(inputs)))
        yield from update_ui(chatbot=chatbot, history=history, msg="api_key已导入") # 刷新界面
        return
    elif not is_any_api_key(chatbot._cookies['api_key']):
        chatbot.append((inputs, "缺少api_key。\n\n1. 临时解决方案：直接在输入区键入api_key，然后回车提交。\n\n2. 长效解决方案：在config.py中配置。"))
        yield from update_ui(chatbot=chatbot, history=history, msg="缺少api_key") # 刷新界面
        return
    if not have_recent_file:
        chatbot.append((inputs, "没有检测到任何近期上传的图像文件，请上传jpg格式的图片，此外，请注意拓展名需要小写"))
        yield from update_ui(chatbot=chatbot, history=history, msg="等待图片") # 刷新界面
        return
    if os.path.exists(inputs):
        chatbot.append((inputs, "已经接收到您上传的文件，您不需要再重复强调该文件的路径了，请直接输入您的问题。"))
        yield from update_ui(chatbot=chatbot, history=history, msg="等待指令") # 刷新界面
        return


    user_input = inputs
    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    raw_input = inputs
    def make_media_input(inputs, image_paths):
        for image_path in image_paths:
            inputs = inputs + f'<br/><br/><div align="center"><img src="file={os.path.abspath(image_path)}"></div>'
        return inputs
    chatbot.append((make_media_input(inputs, image_paths), ""))
    yield from update_ui(chatbot=chatbot, history=history, msg="等待响应") # 刷新界面

    # check mis-behavior
    if is_the_upload_folder(user_input):
        chatbot[-1] = (inputs, f"[Local Message] 检测到操作错误！当您上传文档之后，需点击“**函数插件区**”按钮进行处理，请勿点击“提交”按钮或者“基础功能区”按钮。")
        yield from update_ui(chatbot=chatbot, history=history, msg="正常") # 刷新界面
        time.sleep(2)

    try:
        headers, payload, api_key = generate_payload(inputs, llm_kwargs, history, system_prompt, image_paths)
    except RuntimeError as e:
        chatbot[-1] = (inputs, f"您提供的api-key不满足要求，不包含任何可用于{llm_kwargs['llm_model']}的api-key。您可能选择了错误的模型或请求源。")
        yield from update_ui(chatbot=chatbot, history=history, msg="api-key不满足要求") # 刷新界面
        return

    # 检查endpoint是否合法
    try:
        from .bridge_all import model_info
        endpoint = verify_endpoint(model_info[llm_kwargs['llm_model']]['endpoint'])
    except:
        tb_str = '```\n' + trimmed_format_exc() + '```'
        chatbot[-1] = (inputs, tb_str)
        yield from update_ui(chatbot=chatbot, history=history, msg="Endpoint不满足要求") # 刷新界面
        return

    history.append(make_media_input(inputs, image_paths))
    history.append("")

    retry = 0
    while True:
        try:
            # make a POST request to the API endpoint, stream=True
            response = requests.post(endpoint, headers=headers, proxies=proxies,
                                    json=payload, stream=True, timeout=TIMEOUT_SECONDS);break
        except:
            retry += 1
            chatbot[-1] = ((chatbot[-1][0], timeout_bot_msg))
            retry_msg = f"，正在重试 ({retry}/{MAX_RETRY}) ……" if MAX_RETRY > 0 else ""
            yield from update_ui(chatbot=chatbot, history=history, msg="请求超时"+retry_msg) # 刷新界面
            if retry > MAX_RETRY: raise TimeoutError

    gpt_replying_buffer = ""

    is_head_of_the_stream = True
    if stream:
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
                    yield from update_ui(chatbot=chatbot, history=history, msg="检测到有缺陷的非OpenAI官方接口，建议选择更稳定的接口。")
                    break
                # 其他情况，直接返回报错
                chatbot, history = handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg, api_key)
                yield from update_ui(chatbot=chatbot, history=history, msg="非OpenAI官方接口返回了错误:" + chunk.decode()) # 刷新界面
                return

            # 提前读取一些信息 （用于判断异常）
            chunk_decoded, chunkjson, has_choices, choice_valid, has_content, has_role = decode_chunk(chunk)

            if is_head_of_the_stream and (r'"object":"error"' not in chunk_decoded) and (r"content" not in chunk_decoded):
                # 数据流的第一帧不携带content
                is_head_of_the_stream = False; continue

            if chunk:
                try:
                    if has_choices and not choice_valid:
                        # 一些垃圾第三方接口的出现这样的错误
                        continue
                    # 前者是API2D的结束条件，后者是OPENAI的结束条件
                    if ('data: [DONE]' in chunk_decoded) or (len(chunkjson['choices'][0]["delta"]) == 0):
                        # 判定为数据流的结束，gpt_replying_buffer也写完了
                        lastmsg = chatbot[-1][-1] + f"\n\n\n\n「{llm_kwargs['llm_model']}调用结束，该模型不具备上下文对话能力，如需追问，请及时切换模型。」"
                        yield from update_ui_latest_msg(lastmsg, chatbot, history, delay=1)
                        log_chat(llm_model=llm_kwargs["llm_model"], input_str=inputs, output_str=gpt_replying_buffer)
                        break
                    # 处理数据流的主体
                    status_text = f"finish_reason: {chunkjson['choices'][0].get('finish_reason', 'null')}"
                    # 如果这里抛出异常，一般是文本过长，详情见get_full_error的输出
                    if has_content:
                        # 正常情况
                        gpt_replying_buffer = gpt_replying_buffer + chunkjson['choices'][0]["delta"]["content"]
                    elif has_role:
                        # 一些第三方接口的出现这样的错误，兼容一下吧
                        continue
                    else:
                        # 一些垃圾第三方接口的出现这样的错误
                        gpt_replying_buffer = gpt_replying_buffer + chunkjson['choices'][0]["delta"]["content"]

                    history[-1] = gpt_replying_buffer
                    chatbot[-1] = (history[-2], history[-1])
                    yield from update_ui(chatbot=chatbot, history=history, msg=status_text) # 刷新界面
                except Exception as e:
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json解析不合常规") # 刷新界面
                    chunk = get_full_error(chunk, stream_response)
                    chunk_decoded = chunk.decode()
                    error_msg = chunk_decoded
                    chatbot, history = handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg, api_key)
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json异常" + error_msg) # 刷新界面
                    logger.error(error_msg)
                    return
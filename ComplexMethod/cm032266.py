def predict(
        inputs,
        llm_kwargs,
        plugin_kwargs,
        chatbot,
        history=[],
        system_prompt="",
        stream=True,
        additional_fn=None,
    ):
        """
        发送至chatGPT，流式获取输出。
        用于基础的对话功能。
        inputs 是本次问询的输入
        top_p, temperature是chatGPT的内部调优参数
        history 是之前的对话列表（注意无论是inputs还是history，内容太长了都会触发token数量溢出的错误）
        chatbot 为WebUI中显示的对话列表，修改它，然后yield出去，可以直接修改对话界面内容
        additional_fn代表点击的哪个按钮，按钮见functional.py
        """
        from .bridge_all import model_info
        if len(APIKEY) == 0:
            raise RuntimeError(f"APIKEY为空,请检查配置文件的{APIKEY}")
        if inputs == "":
            inputs = "你好👋"
        if additional_fn is not None:
            from core_functional import handle_core_functionality

            inputs, history = handle_core_functionality(
                additional_fn, inputs, history, chatbot
            )
        logger.info(f"[raw_input] {inputs}")
        chatbot.append((inputs, ""))
        yield from update_ui(
            chatbot=chatbot, history=history, msg="等待响应"
        )  # 刷新界面

        # check mis-behavior
        if is_the_upload_folder(inputs):
            chatbot[-1] = (
                inputs,
                f"[Local Message] 检测到操作错误！当您上传文档之后，需点击“**函数插件区**”按钮进行处理，请勿点击“提交”按钮或者“基础功能区”按钮。",
            )
            yield from update_ui(
                chatbot=chatbot, history=history, msg="正常"
            )  # 刷新界面
            time.sleep(2)

        headers, payload = generate_message(
            input=inputs,
            model=remove_prefix(llm_kwargs["llm_model"]),
            key=APIKEY,
            history=history,
            max_output_token=max_output_token,
            system_prompt=system_prompt,
            temperature=llm_kwargs["temperature"],
        )

        reasoning = model_info[llm_kwargs['llm_model']].get('enable_reasoning', False)

        history.append(inputs)
        history.append("")
        retry = 0
        while True:
            try:
                endpoint = model_info[llm_kwargs["llm_model"]]["endpoint"]
                response = requests.post(
                    endpoint,
                    headers=headers,
                    proxies=None if disable_proxy else proxies,
                    json=payload,
                    stream=True,
                    timeout=TIMEOUT_SECONDS,
                )
                break
            except:
                retry += 1
                chatbot[-1] = (chatbot[-1][0], timeout_bot_msg)
                retry_msg = (
                    f"，正在重试 ({retry}/{MAX_RETRY}) ……" if MAX_RETRY > 0 else ""
                )
                yield from update_ui(
                    chatbot=chatbot, history=history, msg="请求超时" + retry_msg
                )  # 刷新界面
                if retry > MAX_RETRY:
                    raise TimeoutError

        gpt_replying_buffer = ""
        if reasoning:
            gpt_reasoning_buffer = ""

        stream_response = response.iter_lines()
        wait_counter = 0
        while True:
            try:
                chunk = next(stream_response)
            except StopIteration:
                if wait_counter != 0 and gpt_replying_buffer == "":
                    yield from update_ui_latest_msg(lastmsg="模型调用失败 ...", chatbot=chatbot, history=history, msg="failed")
                break
            except requests.exceptions.ConnectionError:
                chunk = next(stream_response)  # 失败了，重试一次？再失败就没办法了。
            response_text, reasoning_content, finish_reason, decoded_chunk = decode_chunk(chunk)
            if decoded_chunk == ': keep-alive':
                wait_counter += 1
                yield from update_ui_latest_msg(lastmsg="等待中 " + "".join(["."] * (wait_counter%10)), chatbot=chatbot, history=history, msg="waiting ...")
                continue
            # 返回的数据流第一次为空，继续等待
            if response_text == "" and (reasoning == False or reasoning_content == "") and finish_reason != "False":
                status_text = f"finish_reason: {finish_reason}"
                yield from update_ui(
                    chatbot=chatbot, history=history, msg=status_text
                )
                continue
            if chunk:
                try:
                    if response_text == "API_ERROR" and (
                        finish_reason != "False" or finish_reason != "stop"
                    ):
                        chunk = get_full_error(chunk, stream_response)
                        chunk_decoded = chunk.decode()
                        chatbot[-1] = (
                            chatbot[-1][0],
                            f"[Local Message] {finish_reason}, 获得以下报错信息：\n"
                            + chunk_decoded,
                        )
                        yield from update_ui(
                            chatbot=chatbot,
                            history=history,
                            msg="API异常:" + chunk_decoded,
                        )  # 刷新界面
                        logger.error(chunk_decoded)
                        return

                    if finish_reason == "stop":
                        logger.info(f"[response] {gpt_replying_buffer}")
                        break
                    status_text = f"finish_reason: {finish_reason}"
                    if reasoning:
                        gpt_replying_buffer += response_text
                        gpt_reasoning_buffer += reasoning_content
                        paragraphs = ''.join([f'<p style="margin: 1.25em 0;">{line}</p>' for line in gpt_reasoning_buffer.split('\n')])
                        history[-1] = f'<div class="reasoning_process">{paragraphs}</div>\n\n---\n\n' + gpt_replying_buffer
                    else:
                        gpt_replying_buffer += response_text
                        # 如果这里抛出异常，一般是文本过长，详情见get_full_error的输出
                        history[-1] = gpt_replying_buffer
                    chatbot[-1] = (history[-2], history[-1])
                    yield from update_ui(
                        chatbot=chatbot, history=history, msg=status_text
                    )  # 刷新界面
                except Exception as e:
                    yield from update_ui(
                        chatbot=chatbot, history=history, msg="Json解析不合常规"
                    )  # 刷新界面
                    chunk = get_full_error(chunk, stream_response)
                    chunk_decoded = chunk.decode()
                    chatbot[-1] = (
                        chatbot[-1][0],
                        "[Local Message] 解析错误,获得以下报错信息：\n" + chunk_decoded,
                    )
                    yield from update_ui(
                        chatbot=chatbot, history=history, msg="Json异常" + chunk_decoded
                    )  # 刷新界面
                    logger.error(chunk_decoded)
                    return
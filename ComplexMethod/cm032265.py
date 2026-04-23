def predict_no_ui_long_connection(
        inputs,
        llm_kwargs,
        history=[],
        sys_prompt="",
        observe_window=None,
        console_silence=False,
    ):
        """
        发送至chatGPT，等待回复，一次性完成，不显示中间过程。但内部用stream的方法避免中途网线被掐。
        inputs：
            是本次问询的输入
        sys_prompt:
            系统静默prompt
        llm_kwargs：
            chatGPT的内部调优参数
        history：
            是之前的对话列表
        observe_window = None：
            用于负责跨越线程传递已经输出的部分，大部分时候仅仅为了fancy的视觉效果，留空即可。observe_window[0]：观测窗。observe_window[1]：看门狗
        """
        from .bridge_all import model_info
        watch_dog_patience = 5  # 看门狗的耐心，设置5秒不准咬人 (咬的也不是人)
        if len(APIKEY) == 0:
            raise RuntimeError(f"APIKEY为空,请检查配置文件的{APIKEY}")
        if inputs == "":
            inputs = "你好👋"


        headers, payload = generate_message(
            input=inputs,
            model=remove_prefix(llm_kwargs["llm_model"]),
            key=APIKEY,
            history=history,
            max_output_token=max_output_token,
            system_prompt=sys_prompt,
            temperature=llm_kwargs["temperature"],
        )

        reasoning = model_info[llm_kwargs['llm_model']].get('enable_reasoning', False)

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
                traceback.print_exc()
                if retry > MAX_RETRY:
                    raise TimeoutError
                if MAX_RETRY != 0:
                    logger.error(f"请求超时，正在重试 ({retry}/{MAX_RETRY}) ……")

        result = ""
        finish_reason = ""
        if reasoning:
            reasoning_buffer = ""

        stream_response = response.iter_lines()
        while True:
            try:
                chunk = next(stream_response)
            except StopIteration:
                if result == "":
                    raise RuntimeError(f"获得空的回复，可能原因:{finish_reason}")
                break
            except requests.exceptions.ConnectionError:
                chunk = next(stream_response)  # 失败了，重试一次？再失败就没办法了。
            response_text, reasoning_content, finish_reason, decoded_chunk = decode_chunk(chunk)
            # 返回的数据流第一次为空，继续等待
            if response_text == "" and (reasoning == False or reasoning_content == "") and finish_reason != "False":
                continue
            if response_text == "API_ERROR" and (
                finish_reason != "False" or finish_reason != "stop"
            ):
                chunk = get_full_error(chunk, stream_response)
                chunk_decoded = chunk.decode()
                logger.error(chunk_decoded)
                raise RuntimeError(
                    f"API异常,请检测终端输出。可能的原因是:{finish_reason}"
                )
            if chunk:
                try:
                    if finish_reason == "stop":
                        if not console_silence:
                            print(f"[response] {result}")
                        break
                    result += response_text
                    if reasoning:
                        reasoning_buffer += reasoning_content
                    if observe_window is not None:
                        # 观测窗，把已经获取的数据显示出去
                        if len(observe_window) >= 1:
                            observe_window[0] += response_text
                        # 看门狗，如果超过期限没有喂狗，则终止
                        if len(observe_window) >= 2:
                            if (time.time() - observe_window[1]) > watch_dog_patience:
                                raise RuntimeError("用户取消了程序。")
                except Exception as e:
                    chunk = get_full_error(chunk, stream_response)
                    chunk_decoded = chunk.decode()
                    error_msg = chunk_decoded
                    logger.error(error_msg)
                    raise RuntimeError("Json解析不合常规")
        if reasoning:
            paragraphs = ''.join([f'<p style="margin: 1.25em 0;">{line}</p>' for line in reasoning_buffer.split('\n')])
            return f'''<div class="reasoning_process" >{paragraphs}</div>\n\n''' + result
        return result
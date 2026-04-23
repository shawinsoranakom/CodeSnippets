def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=None, console_silence=False):
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
    watch_dog_patience = 5 # 看门狗的耐心, 设置5秒即可
    if len(ANTHROPIC_API_KEY) == 0:
        raise RuntimeError("没有设置ANTHROPIC_API_KEY选项")
    if inputs == "":     inputs = "空空如也的输入栏"
    headers, message = generate_payload(inputs, llm_kwargs, history, sys_prompt, image_paths=None)
    retry = 0


    while True:
        try:
            # make a POST request to the API endpoint, stream=False
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
    result = ''
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
                    # logger.info(f'[response] {result}')
                    break
                else:
                    if chunkjson and chunkjson['type'] == 'content_block_delta':
                        result += chunkjson['delta']['text']
                        if observe_window is not None:
                            # 观测窗，把已经获取的数据显示出去
                            if len(observe_window) >= 1:
                                observe_window[0] += chunkjson['delta']['text']
                            # 看门狗，如果超过期限没有喂狗，则终止
                            if len(observe_window) >= 2:
                                if (time.time()-observe_window[1]) > watch_dog_patience:
                                    raise RuntimeError("用户取消了程序。")
            except Exception as e:
                chunk = get_full_error(chunk, stream_response)
                chunk_decoded = chunk.decode()
                error_msg = chunk_decoded
                logger.error(error_msg)
                raise RuntimeError("Json解析不合常规")

    return result
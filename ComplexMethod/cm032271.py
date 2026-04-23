def predict_no_ui_long_connection(inputs:str, llm_kwargs:dict, history:list=[], sys_prompt:str="", observe_window:list=None, console_silence:bool=False):
    """
    发送，等待回复，一次性完成，不显示中间过程。但内部用stream的方法避免中途网线被掐。
    inputs：
        是本次问询的输入
    sys_prompt:
        系统静默prompt
    llm_kwargs：
        内部调优参数
    history：
        是之前的对话列表
    observe_window = None：
        用于负责跨越线程传递已经输出的部分，大部分时候仅仅为了fancy的视觉效果，留空即可。observe_window[0]：观测窗。observe_window[1]：看门狗
    """
    watch_dog_patience = 5 # 看门狗的耐心, 设置5秒即可
    headers, payload = generate_payload(inputs, llm_kwargs, history, system_prompt=sys_prompt, stream=True)
    retry = 0
    while True:
        try:
            # make a POST request to the API endpoint, stream=False
            from .bridge_all import model_info
            endpoint = verify_endpoint(model_info[llm_kwargs['llm_model']]['endpoint'])
            response = requests.post(endpoint, headers=headers, proxies=proxies,
                                    json=payload, stream=True, timeout=TIMEOUT_SECONDS); break
        except requests.exceptions.ReadTimeout as e:
            retry += 1
            traceback.print_exc()
            if retry > MAX_RETRY: raise TimeoutError
            if MAX_RETRY!=0: logger.error(f'请求超时，正在重试 ({retry}/{MAX_RETRY}) ……')

    stream_response = response.iter_lines()
    result = ''
    json_data = None
    while True:
        try: chunk = next(stream_response)
        except StopIteration:
            break
        except requests.exceptions.ConnectionError:
            chunk = next(stream_response) # 失败了，重试一次？再失败就没办法了。
        chunk_decoded, chunkjson, has_choices, choice_valid, has_content, has_role = decode_chunk(chunk)
        if chunkjson['event_type'] == 'stream-start': continue
        if chunkjson['event_type'] == 'text-generation':
            result += chunkjson["text"]
            if not console_silence: print(chunkjson["text"], end='')
            if observe_window is not None:
                # 观测窗，把已经获取的数据显示出去
                if len(observe_window) >= 1:
                    observe_window[0] += chunkjson["text"]
                # 看门狗，如果超过期限没有喂狗，则终止
                if len(observe_window) >= 2:
                    if (time.time()-observe_window[1]) > watch_dog_patience:
                        raise RuntimeError("用户取消了程序。")
        if chunkjson['event_type'] == 'stream-end': break
    return result
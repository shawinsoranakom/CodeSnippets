def predict_no_ui_long_connection(inputs:str, llm_kwargs:dict, history:list=[], sys_prompt:str="", observe_window:list=None, console_silence:bool=False):
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
    from request_llms.bridge_all import model_info

    watch_dog_patience = 5 # 看门狗的耐心, 设置5秒即可

    if model_info[llm_kwargs['llm_model']].get('openai_disable_stream', False): stream = False
    else: stream = True

    headers, payload = generate_payload(inputs, llm_kwargs, history, system_prompt=sys_prompt, stream=stream)
    retry = 0
    while True:
        try:
            # make a POST request to the API endpoint, stream=False
            endpoint = verify_endpoint(model_info[llm_kwargs['llm_model']]['endpoint'])
            response = requests.post(endpoint, headers=headers, proxies=proxies,
                                    json=payload, stream=stream, timeout=TIMEOUT_SECONDS); break
        except requests.exceptions.ReadTimeout as e:
            retry += 1
            traceback.print_exc()
            if retry > MAX_RETRY: raise TimeoutError
            if MAX_RETRY!=0: logger.error(f'请求超时，正在重试 ({retry}/{MAX_RETRY}) ……')

    if not stream:
        # 该分支仅适用于不支持stream的o1模型，其他情形一律不适用
        chunkjson = json.loads(response.content.decode())
        gpt_replying_buffer = chunkjson['choices'][0]["message"]["content"]
        return gpt_replying_buffer

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
        if len(chunk_decoded)==0: continue
        if not chunk_decoded.startswith('data:'):
            error_msg = get_full_error(chunk, stream_response).decode()
            if "reduce the length" in error_msg:
                raise ConnectionAbortedError("OpenAI拒绝了请求:" + error_msg)
            elif """type":"upstream_error","param":"307""" in error_msg:
                raise ConnectionAbortedError("正常结束，但显示Token不足，导致输出不完整，请削减单次输入的文本量。")
            else:
                raise RuntimeError("OpenAI拒绝了请求：" + error_msg)
        if ('data: [DONE]' in chunk_decoded): break # api2d & one-api 正常完成
        # 提前读取一些信息 （用于判断异常）
        if has_choices and not choice_valid:
            # 一些垃圾第三方接口的出现这样的错误
            continue
        json_data = chunkjson['choices'][0]
        delta = json_data["delta"]

        if len(delta) == 0:
            is_termination_certain = False
            if (has_choices) and (chunkjson['choices'][0].get('finish_reason', 'null') == 'stop'): is_termination_certain = True
            if is_termination_certain: break
            else: continue # 对于不符合规范的狗屎接口，这里需要继续

        if (not has_content) and has_role: continue
        if (not has_content) and (not has_role): continue # raise RuntimeError("发现不标准的第三方接口："+delta)
        if has_content: # has_role = True/False
            result += delta["content"]
            if not console_silence: print(delta["content"], end='')
            if observe_window is not None:
                # 观测窗，把已经获取的数据显示出去
                if len(observe_window) >= 1:
                    observe_window[0] += delta["content"]
                # 看门狗，如果超过期限没有喂狗，则终止
                if len(observe_window) >= 2:
                    if (time.time()-observe_window[1]) > watch_dog_patience:
                        raise RuntimeError("用户取消了程序。")
        else: raise RuntimeError("意外Json结构："+delta)

    finish_reason = json_data.get('finish_reason', None) if json_data else None
    if finish_reason == 'content_filter':
        raise RuntimeError("由于提问含不合规内容被过滤。")
    if finish_reason == 'length':
        raise ConnectionAbortedError("正常结束，但显示Token不足，导致输出不完整，请削减单次输入的文本量。")

    return result
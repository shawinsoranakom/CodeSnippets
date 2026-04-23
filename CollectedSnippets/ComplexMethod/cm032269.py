def generate(self, inputs, llm_kwargs, history, system_prompt):
        # import _thread as thread
        from dashscope import Generation
        top_p = llm_kwargs.get('top_p', 0.8)
        if top_p == 0: top_p += 1e-5
        if top_p == 1: top_p -= 1e-5

        model_name = llm_kwargs['llm_model']
        if model_name.startswith(model_prefix_to_remove): model_name = model_name[len(model_prefix_to_remove):]

        self.reasoning_buf = ""
        self.result_buf = ""
        responses = Generation.call(
            model=model_name,
            messages=generate_message_payload(inputs, llm_kwargs, history, system_prompt),
            top_p=top_p,
            temperature=llm_kwargs.get('temperature', 1.0),
            result_format='message',
            stream=True,
            incremental_output=True
        )

        for response in responses:
            if response.status_code == HTTPStatus.OK:
                if response.output.choices[0].finish_reason == 'stop':
                    try:
                        self.result_buf += response.output.choices[0].message.content
                    except:
                        pass
                    yield self.format_reasoning(self.reasoning_buf, self.result_buf)
                    break
                elif response.output.choices[0].finish_reason == 'length':
                    self.result_buf += "[Local Message] 生成长度过长，后续输出被截断"
                    yield self.format_reasoning(self.reasoning_buf, self.result_buf)
                    break
                else:
                    try:
                        contain_reasoning = hasattr(response.output.choices[0].message, 'reasoning_content')
                    except:
                        contain_reasoning = False
                    if contain_reasoning:
                        self.reasoning_buf += response.output.choices[0].message.reasoning_content
                    self.result_buf += response.output.choices[0].message.content
                    yield self.format_reasoning(self.reasoning_buf, self.result_buf)
            else:
                self.result_buf += f"[Local Message] 请求错误：状态码：{response.status_code}，错误码:{response.code}，消息：{response.message}"
                yield self.format_reasoning(self.reasoning_buf, self.result_buf)
                break

        # 耗尽generator避免报错
        while True:
            try: next(responses)
            except: break

        return self.result_buf
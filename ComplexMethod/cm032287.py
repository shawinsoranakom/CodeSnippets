def generate_message_payload(
        self, inputs, llm_kwargs, history, system_prompt, image_base64_array:list=[], has_multimodal_capacity:bool=False
    ) -> Tuple[Dict, Dict]:
        messages = [
            # {"role": "system", "parts": [{"text": system_prompt}]},  # gemini 不允许对话轮次为偶数，所以这个没有用，看后续支持吧。。。
            # {"role": "user", "parts": [{"text": ""}]},
            # {"role": "model", "parts": [{"text": ""}]}
        ]
        self.url_gemini = self.url_gemini.replace(
            "%m", llm_kwargs["llm_model"]
        ).replace("%k", get_conf("GEMINI_API_KEY"))
        header = {"Content-Type": "application/json"}

        if has_multimodal_capacity:
            enable_multimodal_capacity = (len(image_base64_array) > 0) or any([contain_base64(h) for h in history])
        else:
            enable_multimodal_capacity = False

        if not enable_multimodal_capacity:
            messages.extend(
                self.__conversation_history(history, llm_kwargs, enable_multimodal_capacity)
            )  # 处理 history

        messages.append(self.__conversation_user(inputs, llm_kwargs, enable_multimodal_capacity))  # 处理用户对话
        stop_sequences = str(llm_kwargs.get("stop", "")).split(" ")
        # 过滤空字符串并确保至少有一个停止序列
        stop_sequences = [s for s in stop_sequences if s]
        if not stop_sequences:
            payload = {
                "contents": messages,
                "generationConfig": {
                    "temperature": llm_kwargs.get("temperature", 1),
                    "topP": llm_kwargs.get("top_p", 0.8),
                    "topK": 10,
                },
            }
        else:
            payload = {
                "contents": messages,
                "generationConfig": {
                    # "maxOutputTokens": llm_kwargs.get("max_token", 1024),
                    "stopSequences": stop_sequences,
                    "temperature": llm_kwargs.get("temperature", 1),
                    "topP": llm_kwargs.get("top_p", 0.8),
                    "topK": 10,
                },
            }

        return header, payload
def create_blocking_request(self, inputs, llm_kwargs, history, system_prompt, use_image_api):
        if llm_kwargs['llm_model'] == 'sparkv2':
            gpt_url = self.gpt_url_v2
        elif llm_kwargs['llm_model'] == 'sparkv3':
            gpt_url = self.gpt_url_v3
        elif llm_kwargs['llm_model'] == 'sparkv3.5':
            gpt_url = self.gpt_url_v35
        elif llm_kwargs['llm_model'] == 'sparkv4':
            gpt_url = self.gpt_url_v4
        else:
            gpt_url = self.gpt_url
        file_manifest = []
        if use_image_api and llm_kwargs.get('most_recent_uploaded'):
            if llm_kwargs['most_recent_uploaded'].get('path'):
                file_manifest = get_pictures_list(llm_kwargs['most_recent_uploaded']['path'])
                if len(file_manifest) > 0:
                    logger.info('正在使用讯飞图片理解API')
                    gpt_url = self.gpt_url_img
        wsParam = Ws_Param(self.appid, self.api_key, self.api_secret, gpt_url)
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()

        # 收到websocket连接建立的处理
        def on_open(ws):
            import _thread as thread
            thread.start_new_thread(run, (ws,))
        def run(ws, *args):
            data = json.dumps(gen_params(ws.appid, *ws.all_args, file_manifest))
            ws.send(data)

        # 收到websocket消息的处理
        def on_message(ws, message):
            data = json.loads(message)
            code = data['header']['code']
            if code != 0:
                logger.error(f'请求错误: {code}, {data}')
                self.result_buf += str(data)
                ws.close()
                self.time_to_exit_event.set()
            else:
                choices = data["payload"]["choices"]
                status = choices["status"]
                content = choices["text"][0]["content"]
                ws.content += content
                self.result_buf += content
                if status == 2:
                    ws.close()
                    self.time_to_exit_event.set()
            self.time_to_yield_event.set()

        # 收到websocket错误的处理
        def on_error(ws, error):
            logger.error("error:", error)
            self.time_to_exit_event.set()

        # 收到websocket关闭的处理
        def on_close(ws, *args):
            self.time_to_exit_event.set()

        # websocket
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        ws.appid = self.appid
        ws.content = ""
        ws.all_args = (inputs, llm_kwargs, history, system_prompt)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
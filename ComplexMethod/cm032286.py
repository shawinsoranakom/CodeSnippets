def run(self):
        # 子进程执行
        # 第一次运行，加载参数
        retry = 0
        while True:
            try:
                if self.chatglmft_model is None:
                    from transformers import AutoConfig
                    import torch
                    # conf = 'request_llms/current_ptune_model.json'
                    # if not os.path.exists(conf): raise RuntimeError('找不到微调模型信息')
                    # with open(conf, 'r', encoding='utf8') as f:
                    #     model_args = json.loads(f.read())
                    CHATGLM_PTUNING_CHECKPOINT = get_conf('CHATGLM_PTUNING_CHECKPOINT')
                    assert os.path.exists(CHATGLM_PTUNING_CHECKPOINT), "找不到微调模型检查点"
                    conf = os.path.join(CHATGLM_PTUNING_CHECKPOINT, "config.json")
                    with open(conf, 'r', encoding='utf8') as f:
                        model_args = json.loads(f.read())
                    if 'model_name_or_path' not in model_args:
                        model_args['model_name_or_path'] = model_args['_name_or_path']
                    self.chatglmft_tokenizer = AutoTokenizer.from_pretrained(
                        model_args['model_name_or_path'], trust_remote_code=True)
                    config = AutoConfig.from_pretrained(
                        model_args['model_name_or_path'], trust_remote_code=True)

                    config.pre_seq_len = model_args['pre_seq_len']
                    config.prefix_projection = model_args['prefix_projection']

                    logger.info(f"Loading prefix_encoder weight from {CHATGLM_PTUNING_CHECKPOINT}")
                    model = AutoModel.from_pretrained(model_args['model_name_or_path'], config=config, trust_remote_code=True)
                    prefix_state_dict = torch.load(os.path.join(CHATGLM_PTUNING_CHECKPOINT, "pytorch_model.bin"))
                    new_prefix_state_dict = {}
                    for k, v in prefix_state_dict.items():
                        if k.startswith("transformer.prefix_encoder."):
                            new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
                    model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)

                    if model_args['quantization_bit'] is not None and model_args['quantization_bit'] != 0:
                        logger.info(f"Quantized to {model_args['quantization_bit']} bit")
                        model = model.quantize(model_args['quantization_bit'])
                    model = model.cuda()
                    if model_args['pre_seq_len'] is not None:
                        # P-tuning v2
                        model.transformer.prefix_encoder.float()
                    self.chatglmft_model = model.eval()

                    break
                else:
                    break
            except Exception as e:
                retry += 1
                if retry > 3:
                    self.child.send('[Local Message] Call ChatGLMFT fail 不能正常加载ChatGLMFT的参数。')
                    raise RuntimeError("不能正常加载ChatGLMFT的参数！")

        while True:
            # 进入任务等待状态
            kwargs = self.child.recv()
            # 收到消息，开始请求
            try:
                for response, history in self.chatglmft_model.stream_chat(self.chatglmft_tokenizer, **kwargs):
                    self.child.send(response)
                    # # 中途接收可能的终止指令（如果有的话）
                    # if self.child.poll():
                    #     command = self.child.recv()
                    #     if command == '[Terminate]': break
            except:
                from toolbox import trimmed_format_exc
                self.child.send('[Local Message] Call ChatGLMFT fail.' + '\n```\n' + trimmed_format_exc() + '\n```\n')
            # 请求处理结束，开始下一个循环
            self.child.send('[Finish]')
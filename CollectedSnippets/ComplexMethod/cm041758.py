async def _generate(
        self,
        messages: list[dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[str] = None,
        **input_kwargs,
    ) -> AsyncGenerator[str, None]:
        paired = messages + [{"role": "assistant", "content": ""}]
        prompt_ids, _ = self.template.encode_oneturn(self.tokenizer, paired, system, tools)
        prompt_len = len(prompt_ids)

        max_length: Optional[int] = input_kwargs.pop("max_length", None)
        max_new_tokens: Optional[int] = input_kwargs.pop("max_new_tokens", None)

        if "max_new_tokens" in self.generating_args:
            max_tokens = int(self.generating_args["max_new_tokens"])
        elif "max_length" in self.generating_args:
            gl = int(self.generating_args["max_length"])
            max_tokens = gl - prompt_len if gl > prompt_len else 1
        else:
            max_tokens = self.max_new_tokens or 256

        if max_length is not None:
            max_tokens = max(max_length - prompt_len, 1)
        if max_new_tokens is not None:
            max_tokens = int(max_new_tokens)
        max_tokens = max(1, int(max_tokens))

        if self.mode == "long_context":
            max_len_cfg = Config().long_context_config["max_seq_len"]
            need = prompt_len + max_tokens
            assert max_len_cfg > need, f"please set max_seq_len > {need} in ~/.ktransformers/config.yaml"

        device = next(self.model.parameters()).device
        input_tensor = torch.tensor([prompt_ids], dtype=torch.long, device=device)
        if self.force_think:
            think = torch.tensor(
                [self.tokenizer.encode("<think>\n", add_special_tokens=False)], dtype=torch.long, device=device
            )
            input_tensor = torch.cat([input_tensor, think], dim=1)

        use_flashinfer = (
            platform.system() != "Windows"
            and getattr(self.model.config, "architectures", [""])[0]
            in {"DeepseekV2ForCausalLM", "DeepseekV3ForCausalLM"}
            and flashinfer_enabled
            and get_compute_capability() >= 8
            and device_manager.gpu_vendor == GPUVendor.NVIDIA
        )

        def make_gen():
            if use_flashinfer:
                return prefill_and_generate_capture(
                    self.model,
                    self.tokenizer,
                    input_tensor,
                    max_tokens,
                    self.use_cuda_graph,
                    mode=self.mode,
                    force_think=self.force_think,
                    chunk_size=self.chunk_size,
                    use_flashinfer_mla=True,
                    num_heads=self.model.config.num_attention_heads,
                    head_dim_ckv=getattr(self.model.config, "kv_lora_rank", 0),
                    head_dim_kpe=getattr(self.model.config, "qk_rope_head_dim", 0),
                    q_head_dim=getattr(self.model.config, "qk_rope_head_dim", 0)
                    + getattr(self.model.config, "qk_nope_head_dim", 0),
                    echo_stream=False,
                )
            else:
                return prefill_and_generate_capture(
                    self.model,
                    self.tokenizer,
                    input_tensor,
                    max_tokens,
                    self.use_cuda_graph,
                    mode=self.mode,
                    force_think=self.force_think,
                    chunk_size=self.chunk_size,
                    echo_stream=False,
                )

        loop = asyncio.get_running_loop()
        q: asyncio.Queue[Optional[str]] = asyncio.Queue()

        def producer():
            try:
                gen = make_gen()
                if hasattr(gen, "__aiter__"):

                    async def drain_async():
                        async for t in gen:
                            loop.call_soon_threadsafe(q.put_nowait, t if isinstance(t, str) else str(t))

                    asyncio.run(drain_async())
                elif hasattr(gen, "__iter__"):
                    for t in gen:
                        loop.call_soon_threadsafe(q.put_nowait, t if isinstance(t, str) else str(t))
                else:
                    loop.call_soon_threadsafe(q.put_nowait, gen if isinstance(gen, str) else str(gen))
            finally:
                loop.call_soon_threadsafe(q.put_nowait, None)

        Thread(target=producer, daemon=True).start()

        while True:
            item = await q.get()
            if item is None:
                break
            yield item
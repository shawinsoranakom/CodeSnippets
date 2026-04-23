def _read_gguf_metadata(self, gguf_path: str) -> None:
        """Read context_length, architecture params, and chat_template from a GGUF header.

        Parses only the KV pairs we need (~30ms even for multi-GB files).
        For split GGUFs, metadata is always in shard 1.
        """
        # Reset metadata from any previously loaded model so stale flags
        # (eg _supports_reasoning) do not carry over when switching models.
        self._context_length = None
        self._chat_template = None
        self._supports_reasoning = False
        self._reasoning_always_on = False
        self._supports_tools = False
        self._n_layers = None
        self._n_kv_heads = None
        self._n_heads = None
        self._embedding_length = None
        self._kv_key_length = None
        self._kv_value_length = None
        self._sliding_window = None
        self._full_attention_interval = None
        self._kv_lora_rank = None
        self._key_length_mla = None
        self._ssm_inner_size = None
        self._ssm_state_size = None

        try:
            WANTED = {"general.architecture", "tokenizer.chat_template"}
            # Additional arch-specific keys are added dynamically once
            # we know the architecture name.
            arch_keys: dict[str, str] = {}  # gguf_key -> attribute name
            arch = None

            with open(gguf_path, "rb") as f:
                magic = struct.unpack("<I", f.read(4))[0]
                if magic != 0x46554747:  # b"GGUF" as little-endian u32
                    return
                _version = struct.unpack("<I", f.read(4))[0]
                _tensor_count, kv_count = struct.unpack("<QQ", f.read(16))

                for _ in range(kv_count):
                    key_len = struct.unpack("<Q", f.read(8))[0]
                    key = f.read(key_len).decode("utf-8")
                    vtype = struct.unpack("<I", f.read(4))[0]

                    if key in WANTED or key in arch_keys:
                        # Read this value
                        if vtype == 8:  # STRING
                            slen = struct.unpack("<Q", f.read(8))[0]
                            val_s = f.read(slen).decode("utf-8")
                            if key == "general.architecture":
                                arch = val_s
                                # Register arch-specific keys to look for
                                arch_keys = {
                                    f"{arch}.context_length": "context_length",
                                    f"{arch}.block_count": "n_layers",
                                    f"{arch}.attention.head_count_kv": "n_kv_heads",
                                    f"{arch}.attention.head_count": "n_heads",
                                    f"{arch}.embedding_length": "embedding_length",
                                    # Architecture-aware KV cache fields
                                    f"{arch}.attention.key_length": "kv_key_length",
                                    f"{arch}.attention.value_length": "kv_value_length",
                                    f"{arch}.attention.sliding_window": "sliding_window",
                                    f"{arch}.full_attention_interval": "full_attention_interval",
                                    f"{arch}.attention.kv_lora_rank": "kv_lora_rank",
                                    f"{arch}.attention.key_length_mla": "key_length_mla",
                                    f"{arch}.ssm.inner_size": "ssm_inner_size",
                                    f"{arch}.ssm.state_size": "ssm_state_size",
                                }
                            elif key == "tokenizer.chat_template":
                                self._chat_template = val_s
                        elif vtype in (4, 10):  # UINT32 or UINT64
                            val_i = (
                                struct.unpack("<I", f.read(4))[0]
                                if vtype == 4
                                else struct.unpack("<Q", f.read(8))[0]
                            )
                            attr = arch_keys.get(key)
                            if attr:
                                setattr(self, f"_{attr}", val_i)
                        else:
                            self._gguf_skip_value(f, vtype)
                    else:
                        self._gguf_skip_value(f, vtype)

            if self._context_length:
                logger.info(f"GGUF metadata: context_length={self._context_length}")
            if self._chat_template:
                logger.info(
                    f"GGUF metadata: chat_template={len(self._chat_template)} chars"
                )
                # Detect thinking/reasoning support from chat template
                tpl = self._chat_template
                if "enable_thinking" in tpl:
                    self._supports_reasoning = True
                    logger.info(
                        "GGUF metadata: model supports reasoning (enable_thinking)"
                    )
                elif "thinking" in tpl:
                    # DeepSeek uses 'thinking' instead of 'enable_thinking'
                    normalized_id = (self._model_identifier or "").lower()
                    if "deepseek" in normalized_id:
                        self._supports_reasoning = True
                        logger.info(
                            "GGUF metadata: model supports reasoning (DeepSeek thinking)"
                        )
                # Models with hardcoded <think> tags or reasoning_content
                # in their chat template always produce thinking output
                # (no toggle to disable it).
                if not self._supports_reasoning:
                    if (
                        "<think>" in tpl
                        and "</think>" in tpl
                        or "reasoning_content" in tpl
                    ):
                        self._supports_reasoning = True
                        self._reasoning_always_on = True
                        logger.info(
                            "GGUF metadata: model always reasons (<think> tags in template)"
                        )
                # Detect tool calling support from chat template
                tool_markers = [
                    "{%- if tools %}",
                    "{%- if tools -%}",
                    "{% if tools %}",
                    "{% if tools -%}",
                    '"role" == "tool"',
                    "'role' == 'tool'",
                    'message.role == "tool"',
                    "message.role == 'tool'",
                ]
                if any(marker in tpl for marker in tool_markers):
                    self._supports_tools = True
                    logger.info("GGUF metadata: model supports tool calling")
        except Exception as e:
            logger.warning(f"Failed to read GGUF metadata: {e}")
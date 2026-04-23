def get_batch_defaults(
        cls,
        world_size: int,
    ) -> tuple[dict[UsageContext | None, int], dict[UsageContext | None, int]]:
        from vllm.usage.usage_lib import UsageContext

        default_max_num_batched_tokens: dict[UsageContext | None, int]
        default_max_num_seqs: dict[UsageContext | None, int]

        # When no user override, set the default values based on the usage
        # context.
        # Use different default values for different hardware.

        # Try to query the device name on the current platform. If it fails,
        # it may be because the platform that imports vLLM is not the same
        # as the platform that vLLM is running on (e.g. the case of scaling
        # vLLM with Ray) and has no GPUs. In this case we use the default
        # values for non-H100/H200 GPUs.
        try:
            device_memory = current_platform.get_device_total_memory()
            device_name = current_platform.get_device_name().lower()
        except Exception:
            # This is only used to set default_max_num_batched_tokens
            device_memory = 0
            device_name = ""

        # NOTE(Kuntai): Setting large `max_num_batched_tokens` for A100 reduces
        # throughput, see PR #17885 for more details.
        # So here we do an extra device name check to prevent such regression.
        if device_memory >= 70 * GiB_bytes and "a100" not in device_name:
            # For GPUs like H100 and MI300x, use larger default values.
            default_max_num_batched_tokens = {
                UsageContext.LLM_CLASS: 16384,
                UsageContext.OPENAI_API_SERVER: 8192,
            }
            default_max_num_seqs = {
                UsageContext.LLM_CLASS: 1024,
                UsageContext.OPENAI_API_SERVER: 1024,
            }
        else:
            # TODO(woosuk): Tune the default values for other hardware.
            default_max_num_batched_tokens = {
                UsageContext.LLM_CLASS: 8192,
                UsageContext.OPENAI_API_SERVER: 2048,
            }
            default_max_num_seqs = {
                UsageContext.LLM_CLASS: 256,
                UsageContext.OPENAI_API_SERVER: 256,
            }

        # tpu specific default values.
        if current_platform.is_tpu():
            chip_name = current_platform.get_device_name()

            if chip_name == "V6E":
                default_max_num_batched_tokens = {
                    UsageContext.LLM_CLASS: 2048,
                    UsageContext.OPENAI_API_SERVER: 1024,
                }
            elif chip_name == "V5E":
                default_max_num_batched_tokens = {
                    UsageContext.LLM_CLASS: 1024,
                    UsageContext.OPENAI_API_SERVER: 512,
                }
            elif chip_name == "V5P":
                default_max_num_batched_tokens = {
                    UsageContext.LLM_CLASS: 512,
                    UsageContext.OPENAI_API_SERVER: 256,
                }

        # cpu specific default values.
        if current_platform.is_cpu():
            default_max_num_batched_tokens = {
                UsageContext.LLM_CLASS: 4096 * world_size,
                UsageContext.OPENAI_API_SERVER: 2048 * world_size,
            }
            default_max_num_seqs = {
                UsageContext.LLM_CLASS: 256 * world_size,
                UsageContext.OPENAI_API_SERVER: 128 * world_size,
            }

        return default_max_num_batched_tokens, default_max_num_seqs
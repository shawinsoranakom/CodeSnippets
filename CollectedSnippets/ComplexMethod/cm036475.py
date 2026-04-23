def test_enabled_ops(
    env: str | None,
    compilation_mode: int,
    backend: str,
    ops_enabled: list[int],
    default_on: bool,
):
    custom_ops = env.split(",") if env else []
    vllm_config = VllmConfig(
        compilation_config=CompilationConfig(
            backend=backend, mode=compilation_mode, custom_ops=custom_ops
        )
    )
    get_cached_compilation_config.cache_clear()
    with set_current_vllm_config(vllm_config):
        assert CustomOp.default_on() == default_on

        ops_enabled = [bool(x) for x in ops_enabled]

        assert RMSNorm(1024).enabled() == ops_enabled[0]
        assert op_registry["rms_norm"].enabled() == ops_enabled[0]

        assert SiluAndMul().enabled() == ops_enabled[1]
        assert op_registry["silu_and_mul"].enabled() == ops_enabled[1]

        assert GeluAndMul().enabled() == ops_enabled[2]
        assert op_registry["gelu_and_mul"].enabled() == ops_enabled[2]

        # If registered, subclasses should follow their own name
        assert Relu3().enabled() == ops_enabled[3]
        assert op_registry["relu3"].enabled() == ops_enabled[3]

        # Unregistered subclass
        class SiluAndMul2(SiluAndMul):
            pass

        # Subclasses should not require registration
        assert SiluAndMul2().enabled() == SiluAndMul().enabled()
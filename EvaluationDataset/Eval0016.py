def require_deepspeed_aio(test_case):
    if not is_deepspeed_available():
        return unittest.skip(reason="test requires deepspeed")(test_case)

    import deepspeed
    from deepspeed.ops.aio import AsyncIOBuilder

    if not deepspeed.ops.__compatible_ops__[AsyncIOBuilder.NAME]:
        return unittest.skip(reason="test requires deepspeed async-io")(test_case)
    else:
        return test_case


if is_deepspeed_available():
    from deepspeed.utils import logger as deepspeed_logger  # noqa
    from deepspeed.utils.zero_to_fp32 import load_state_dict_from_zero_checkpoint
    from transformers.integrations.deepspeed import deepspeed_config, is_deepspeed_zero3_enabled

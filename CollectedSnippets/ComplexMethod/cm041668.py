def add_z3_leaf_module(model: "PreTrainedModel") -> None:
    r"""Set module as a leaf module to skip partitioning in deepspeed zero3."""
    if not is_deepspeed_zero3_enabled():
        return

    model_type = getattr(model.config, "model_type", None)
    text_config = getattr(model.config, "text_config", None)
    text_model_type = getattr(text_config, "model_type", None)

    if model_type == "dbrx":
        from transformers.models.dbrx.modeling_dbrx import DbrxFFN

        _set_z3_leaf_modules(model, [DbrxFFN])

    if model_type == "deepseek_v2":
        # deepseek v2 uses custom code
        _set_z3_leaf_modules(model, ["DeepseekV2MoE"])

    if model_type == "deepseek_v3" or model_type == "kimi_vl":
        # deepseek v3 and kimi vl use custom code
        _set_z3_leaf_modules(model, ["DeepseekV3MoE"])

    if model_type == "ernie4_5_moe":
        from transformers.models.ernie4_5_moe.modeling_ernie4_5_moe import Ernie4_5_MoeSparseMoeBlock

        _set_z3_leaf_modules(model, [Ernie4_5_MoeSparseMoeBlock])

    if model_type == "granitemoe":
        from transformers.models.granitemoe.modeling_granitemoe import GraniteMoeMoE

        _set_z3_leaf_modules(model, [GraniteMoeMoE])

    if model_type == "glm4_moe":
        from transformers.models.glm4_moe.modeling_glm4_moe import Glm4MoeMoE

        _set_z3_leaf_modules(model, [Glm4MoeMoE])

    if model_type == "glm4_moe_lite":
        from transformers.models.glm4_moe_lite.modeling_glm4_moe_lite import Glm4MoeLiteMoE

        _set_z3_leaf_modules(model, [Glm4MoeLiteMoE])

    if model_type == "glm4v_moe":
        from transformers.models.glm4v_moe.modeling_glm4v_moe import Glm4vMoeTextMoE

        _set_z3_leaf_modules(model, [Glm4vMoeTextMoE])

    if model_type == "gpt_oss":
        from transformers.models.gpt_oss.modeling_gpt_oss import GptOssMLP

        _set_z3_leaf_modules(model, [GptOssMLP])

    if model_type == "jamba":
        from transformers.models.jamba.modeling_jamba import JambaSparseMoeBlock

        _set_z3_leaf_modules(model, [JambaSparseMoeBlock])

    if model_type == "jetmoe":
        from transformers.models.jetmoe.modeling_jetmoe import JetMoeMoA, JetMoeMoE

        _set_z3_leaf_modules(model, [JetMoeMoA, JetMoeMoE])

    if model_type == "llama4":
        from transformers.models.llama4.modeling_llama4 import Llama4TextMoe

        _set_z3_leaf_modules(model, [Llama4TextMoe])

    if model_type == "mixtral":
        from transformers.models.mixtral.modeling_mixtral import MixtralSparseMoeBlock

        _set_z3_leaf_modules(model, [MixtralSparseMoeBlock])

    if model_type == "olmoe":
        from transformers.models.olmoe.modeling_olmoe import OlmoeSparseMoeBlock

        _set_z3_leaf_modules(model, [OlmoeSparseMoeBlock])

    if model_type == "phimoe":
        from transformers.models.phimoe.modeling_phimoe import PhimoeSparseMoeBlock

        _set_z3_leaf_modules(model, [PhimoeSparseMoeBlock])

    if model_type == "qwen2_moe":
        from transformers.models.qwen2_moe.modeling_qwen2_moe import Qwen2MoeSparseMoeBlock

        _set_z3_leaf_modules(model, [Qwen2MoeSparseMoeBlock])

    if model_type == "qwen3_moe" or text_model_type == "qwen3_moe":  # internvl 3.5
        from transformers.models.qwen3_moe.modeling_qwen3_moe import Qwen3MoeSparseMoeBlock

        _set_z3_leaf_modules(model, [Qwen3MoeSparseMoeBlock])

    if model_type == "qwen3_vl_moe":
        from transformers.models.qwen3_vl_moe.modeling_qwen3_vl_moe import Qwen3VLMoeTextSparseMoeBlock

        _set_z3_leaf_modules(model, [Qwen3VLMoeTextSparseMoeBlock])

    if model_type in ("qwen3_omni_moe", "qwen3_omni_moe_thinker"):
        from transformers.models.qwen3_omni_moe.modeling_qwen3_omni_moe import Qwen3OmniMoeThinkerTextSparseMoeBlock

        _set_z3_leaf_modules(model, [Qwen3OmniMoeThinkerTextSparseMoeBlock])

    if model_type == "qwen3_next":
        from transformers.models.qwen3_next.modeling_qwen3_next import Qwen3NextSparseMoeBlock

        _set_z3_leaf_modules(model, [Qwen3NextSparseMoeBlock])

    if model_type == "qwen3_5_moe":
        from transformers.models.qwen3_5_moe.modeling_qwen3_5_moe import Qwen3_5MoeSparseMoeBlock

        _set_z3_leaf_modules(model, [Qwen3_5MoeSparseMoeBlock])
def _stack_quantization_states(
        self, model: nn.Module, quant_state_dict: dict
    ) -> dict[str, dict[int, Any]]:
        stacked_quant_state_dict: dict[str, dict[int, Any]] = {}
        # TODO: Change this lazy import to normal import
        # after the checks are updated to run on a new version
        from vllm.model_executor.models.utils import is_pp_missing_parameter

        param_dict = dict(model.named_parameters())
        for quant_param_name in quant_state_dict:
            if is_pp_missing_parameter(quant_param_name, model):
                continue

            non_stacked_param_name = quant_param_name

            shard_index = 0
            for shard_name, (
                weight_name,
                index,
            ) in self.modules_mapping.inverse_packed_mapping.items():
                # Some models, such as MiniCPM V2.5/2.6, contain both
                # module names 'kv_proj' and 'qkv_proj'. To prevent 'kv_proj'
                # from being incorrectly identified as being present in
                # 'vpm.encoder.layers.0.self_attn.qkv_proj.weight
                shard_pos = quant_param_name.find(shard_name)
                can_correct_rename = (shard_pos > 0) and (
                    quant_param_name[shard_pos - 1] == "."
                )
                # If the quant_param_name is packed, it won't occur in the
                # param_dict before renaming.
                new_quant_param_name = quant_param_name.replace(shard_name, weight_name)
                need_rename = (quant_param_name not in param_dict) and (
                    new_quant_param_name in param_dict
                )
                if can_correct_rename and need_rename:
                    shard_index = index
                    quant_param_name = new_quant_param_name
                    break

            # Models like Clip/Siglip may skip some layers in initialization,
            # causing unused quant_param_name in state_dict.
            if quant_param_name not in param_dict:
                continue

            if quant_param_name not in stacked_quant_state_dict:
                stacked_quant_state_dict[quant_param_name] = {}

            stacked_quant_state_dict[quant_param_name][shard_index] = quant_state_dict[
                non_stacked_param_name
            ]
        return stacked_quant_state_dict
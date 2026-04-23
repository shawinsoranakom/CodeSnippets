def _rename_weight_for_modelopt_checkpoint(self, name: str) -> str:
        """Rename weights from ModelOpt llama4 fp8 checkpoints to vLLM
        format."""
        if name.startswith("model.") or name.startswith("language_model.model."):
            renamed = (
                name.replace("model.", "language_model.model.", 1)
                if name.startswith("model.")
                else name
            )
            # Handle expert scale parameters with flat naming
            if "feed_forward.experts." in name and (
                "_input_scale" in name or "_weight_scale" in name
            ):
                # Map checkpoint naming to vLLM's expected naming
                if "down_proj_input_scale" in renamed:
                    return renamed.replace("down_proj_input_scale", "w2_input_scale")
                elif "down_proj_weight_scale" in renamed:
                    return renamed.replace("down_proj_weight_scale", "w2_weight_scale")
                elif "gate_up_proj_input_scale" in renamed:
                    return renamed.replace(
                        "gate_up_proj_input_scale", "w13_input_scale"
                    )
                elif "gate_up_proj_weight_scale" in renamed:
                    return renamed.replace(
                        "gate_up_proj_weight_scale", "w13_weight_scale"
                    )
                return renamed

            # Handle attention scale parameters
            elif "self_attn." in name and (".k_scale" in name or ".v_scale" in name):
                if ".k_proj.k_scale" in renamed:
                    return renamed.replace(".k_proj.k_scale", ".attn.k_scale")
                elif ".v_proj.v_scale" in renamed:
                    return renamed.replace(".v_proj.v_scale", ".attn.v_scale")
                return renamed

            # Standard model.* to language_model.model.* renaming
            return renamed

        elif name.startswith("lm_head.weight"):
            return name.replace("lm_head.weight", "language_model.lm_head.weight")

        return name
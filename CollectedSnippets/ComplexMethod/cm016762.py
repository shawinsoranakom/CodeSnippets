def load_sd(self, sd):
        if "model.layers.47.self_attn.q_norm.weight" in sd:
            return self.gemma3_12b.load_sd(sd)
        else:
            sdo = comfy.utils.state_dict_prefix_replace(sd, {"text_embedding_projection.aggregate_embed.weight": "text_embedding_projection.weight", "text_embedding_projection.": "text_embedding_projection."}, filter_keys=True)
            if len(sdo) == 0:
                sdo = sd

            missing_all = []
            unexpected_all = []

            for prefix, component in [("text_embedding_projection.", self.text_embedding_projection)]:
                component_sd = {k.replace(prefix, ""): v for k, v in sdo.items() if k.startswith(prefix)}
                if component_sd:
                    missing, unexpected = component.load_state_dict(component_sd, strict=False, assign=getattr(self, "can_assign_sd", False))
                    missing_all.extend([f"{prefix}{k}" for k in missing])
                    unexpected_all.extend([f"{prefix}{k}" for k in unexpected])

            if "model.diffusion_model.audio_embeddings_connector.transformer_1d_blocks.2.attn1.to_q.bias" not in sd:  # TODO: remove
                ww = sd.get("model.diffusion_model.audio_embeddings_connector.transformer_1d_blocks.0.attn1.to_q.bias", None)
                if ww is not None:
                    if ww.shape[0] == 3840:
                        self.enable_compat_mode()
                        sdv = comfy.utils.state_dict_prefix_replace(sd, {"model.diffusion_model.video_embeddings_connector.": ""}, filter_keys=True)
                        self.video_embeddings_connector.load_state_dict(sdv, strict=False, assign=getattr(self, "can_assign_sd", False))
                        sda = comfy.utils.state_dict_prefix_replace(sd, {"model.diffusion_model.audio_embeddings_connector.": ""}, filter_keys=True)
                        self.audio_embeddings_connector.load_state_dict(sda, strict=False, assign=getattr(self, "can_assign_sd", False))

            return (missing_all, unexpected_all)
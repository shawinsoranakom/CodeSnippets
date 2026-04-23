def find_hf_name_in_tensor_map(hf_name: str) -> str | None:
            """
            Map HuggingFace parameter name to GGUF tensor name.

            This function handles the mismatch between HF parameter naming
            conventions and gguf-py's expected format:
            1. Strips 'model.' prefix (common in multimodal models)
            2. Converts '_weight' suffix to '.weight' (Gemma3 compatibility)
            3. Searches vision_name_map for multimodal parameters
            4. Falls back to text_name_map for language model parameters

            Args:
                hf_name: Full HuggingFace parameter name (e.g.,
                        'model.multi_modal_projector.mm_soft_emb_norm.weight')

            Returns:
                GGUF tensor name with suffix (e.g., 'mm.soft_emb_norm.weight')
                or None if no mapping found
            """
            # In transformers v5, multimodal models (e.g. Gemma3) wrap
            # all sub-models under an outer 'model.' attribute, producing
            # state_dict keys like 'model.language_model.layers.0...' and
            # 'model.vision_tower.vision_model...'.  Strip this outer
            # prefix so the keys match what gguf-py expects.
            if is_multimodal and hf_name.startswith("model."):
                hf_name = hf_name[6:]  # Remove outer 'model.'

            # Strip 'language_model.' prefix for multimodal models - gguf-py
            # tensor mappings expect parameter names without this prefix.
            # Note: 'model.' prefix should be KEPT for text-only models as
            # gguf-py expects it.
            if hf_name.startswith("language_model."):
                hf_name = hf_name[15:]  # Remove 'language_model.'
                # Re-add 'model.' prefix because gguf-py text tensor maps
                # expect 'model.layers...' format.
                if is_multimodal:
                    hf_name = "model." + hf_name

            # Parse parameter name and suffix
            if hf_name.endswith((".weight", ".bias")):
                base_name, suffix = hf_name.rsplit(".", 1)
            else:
                base_name, suffix = hf_name, ""
                # Handle '_weight' suffix (Gemma3 naming: parameter ends with
                # '_weight' instead of '.weight')
                if base_name.endswith("_weight"):
                    base_name = base_name[:-7]  # Remove '_weight'
                    suffix = "weight"

            gguf_name = None
            # Priority 1: Search vision/projector parameters for multimodal models
            if vision_name_map is not None:
                gguf_name = vision_name_map.get_name(base_name)

            # Priority 2: Search text backbone parameters
            if gguf_name is None:
                gguf_name = text_name_map.get_name(base_name)

            if gguf_name is None:
                return None

            return gguf_name + "." + suffix
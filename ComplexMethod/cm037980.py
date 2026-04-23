def llm_weights_generator():
            nonlocal loaded_weights
            for name, w in weights:
                is_encoder = False
                for k in [
                    "mm_whisper_embeddings",
                    "mm_streams_embeddings.embedding_module",
                ]:
                    is_encoder |= (
                        name.startswith(k)
                        and not name.startswith(f"{k}.tok_embeddings")
                        and not name.startswith(f"{k}.audio_language_projection")
                    )

                for pattern, repl in remapping_rules:
                    if re.fullmatch(pattern, name):
                        name = re.sub(pattern, repl, name)

                if is_encoder:
                    name = self.whisper_encoder.load_weight((name, w))
                    loaded_weights.add(f"whisper_encoder.{name}")
                    continue

                if name in audio_params:
                    param = audio_params[name]
                    with torch.no_grad():
                        default_weight_loader(param, w)
                    loaded_weights.add(name)
                else:
                    yield (name, w)
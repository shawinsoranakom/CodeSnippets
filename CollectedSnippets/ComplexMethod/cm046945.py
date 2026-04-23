def _save_pretrained_merged(self, save_directory, **kwargs):
            # check which adapter files exist before save_pretrained
            adapter_files = ["adapter_model.safetensors", "adapter_config.json"]
            existing_before = {
                f
                for f in adapter_files
                if os.path.exists(os.path.join(save_directory, f))
            }

            # sentence-transformers config and modules only get saved if we call save_pretrained
            self.save_pretrained(save_directory)

            # remove LoRA adapters only if they were created by save_pretrained (not pre-existing)
            for file in adapter_files:
                if file not in existing_before:
                    try:
                        os.remove(os.path.join(save_directory, file))
                    except:
                        pass

            tokenizer = kwargs.pop("tokenizer", self.tokenizer)
            if self.no_modules:
                # fallback for non-sentence-transformers models
                print(
                    "Unsloth: No modules detected. Using standard merge_and_unload for saving..."
                )
                safe_kwargs = kwargs.copy()
                # filter out Unsloth-specific args that are not in huggingface's save_pretrained
                unsloth_args = [
                    "save_method",
                    "temporary_location",
                    "maximum_memory_usage",
                ]
                for k in unsloth_args:
                    safe_kwargs.pop(k, None)

                merged_model = self[0].auto_model.merge_and_unload()
                merged_model.save_pretrained(save_directory, **safe_kwargs)
                if tokenizer is not None:
                    tokenizer.save_pretrained(save_directory)
            else:
                self[0].auto_model.save_pretrained_merged(
                    save_directory, tokenizer = tokenizer, **kwargs
                )

            # add Unsloth branding to the generated README
            try:
                FastSentenceTransformer._add_unsloth_branding(save_directory)
            except Exception as e:
                print(f"Unsloth Warning: Failed to add branding to README: {e}")
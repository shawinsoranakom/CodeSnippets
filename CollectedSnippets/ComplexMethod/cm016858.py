def save(self, clip, filename_prefix, prompt=None, extra_pnginfo=None):
        prompt_info = ""
        if prompt is not None:
            prompt_info = json.dumps(prompt)

        metadata = {}
        if not args.disable_metadata:
            metadata["format"] = "pt"
            metadata["prompt"] = prompt_info
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata[x] = json.dumps(extra_pnginfo[x])

        comfy.model_management.load_models_gpu([clip.load_model()], force_patch_weights=True)
        clip_sd = clip.get_sd()

        for prefix in ["clip_l.", "clip_g.", "clip_h.", "t5xxl.", "pile_t5xl.", "mt5xl.", "umt5xxl.", "t5base.", "gemma2_2b.", "llama.", "hydit_clip.", ""]:
            k = list(filter(lambda a: a.startswith(prefix), clip_sd.keys()))
            current_clip_sd = {}
            for x in k:
                current_clip_sd[x] = clip_sd.pop(x)
            if len(current_clip_sd) == 0:
                continue

            p = prefix[:-1]
            replace_prefix = {}
            filename_prefix_ = filename_prefix
            if len(p) > 0:
                filename_prefix_ = "{}_{}".format(filename_prefix_, p)
                replace_prefix[prefix] = ""
            replace_prefix["transformer."] = ""

            full_output_folder, filename, counter, subfolder, filename_prefix_ = folder_paths.get_save_image_path(filename_prefix_, self.output_dir)

            output_checkpoint = f"{filename}_{counter:05}_.safetensors"
            output_checkpoint = os.path.join(full_output_folder, output_checkpoint)

            current_clip_sd = comfy.utils.state_dict_prefix_replace(current_clip_sd, replace_prefix)

            comfy.utils.save_torch_file(current_clip_sd, output_checkpoint, metadata=metadata)
        return {}
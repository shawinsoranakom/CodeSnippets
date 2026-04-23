def _save_pretrained_torchao(
    self,
    save_directory,
    tokenizer = None,
    torchao_config = None,
    push_to_hub = False,
    token = None,
):
    self.save_pretrained(save_directory)

    # grab inner model
    inner_model = self[0].auto_model
    if hasattr(inner_model, "_orig_mod"):
        inner_model = inner_model._orig_mod

    # merge LoRA first
    if hasattr(inner_model, "merge_and_unload"):
        inner_model = inner_model.merge_and_unload()

    # confirm Transformer path
    transformer_path = "0_Transformer"
    modules_path = os.path.join(save_directory, "modules.json")
    if os.path.exists(modules_path):
        try:
            with open(modules_path, "r") as f:
                modules = json.load(f)
            for m in modules:
                if m.get("type", "").endswith("Transformer"):
                    transformer_path = m.get("path", "")
                    break
        except:
            pass

    transformer_dir = os.path.join(save_directory, transformer_path)
    transformer_dir = os.path.abspath(transformer_dir)

    if tokenizer is None:
        tokenizer = self.tokenizer

    @contextlib.contextmanager
    def patch_unsloth_save():
        original_causal = transformers.AutoModelForCausalLM
        original_rmtree = shutil.rmtree
        # unsloth_save_pretrained_torchao expects AutoModelForCausalLM
        transformers.AutoModelForCausalLM = transformers.AutoModel
        # prevent unsloth from deleting the unquantized model directory
        shutil.rmtree = lambda *args, **kwargs: None
        try:
            yield
        finally:
            # unpatch
            transformers.AutoModelForCausalLM = original_causal
            shutil.rmtree = original_rmtree

    with patch_unsloth_save():
        unsloth_save_pretrained_torchao(
            inner_model,
            transformer_dir,
            tokenizer = tokenizer,
            torchao_config = torchao_config,
            push_to_hub = push_to_hub,
            token = token,
        )

    # avoid `0_Transformer-torchao`, it was either this or fix modules.json
    torchao_dir = transformer_dir + "-torchao"
    if os.path.exists(torchao_dir):
        if not os.path.exists(transformer_dir):
            os.makedirs(transformer_dir, exist_ok = True)

        # move contents
        for item in os.listdir(torchao_dir):
            s = os.path.join(torchao_dir, item)
            d = os.path.join(transformer_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok = True)
            else:
                shutil.copy2(s, d)

        # remove torchao dir
        shutil.rmtree(torchao_dir)

        # remove conflicting safetensors if we brought in bin
        if os.path.exists(os.path.join(transformer_dir, "pytorch_model.bin")):
            safetensors_path = os.path.join(transformer_dir, "model.safetensors")
            if os.path.exists(safetensors_path):
                try:
                    os.remove(safetensors_path)
                except:
                    pass

    try:
        FastSentenceTransformer._add_unsloth_branding(save_directory)
    except:
        pass
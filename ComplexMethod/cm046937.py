def _load_modules(
        model_name,
        token,
        model,
        tokenizer,
        max_seq_length,
        pooling_mode,
        trust_remote_code = False,
    ) -> tuple[OrderedDict, bool]:
        """
        Load modules from modules.json if available, otherwise fallback to hard-coded modules.

        Returns:
            tuple[OrderedDict, bool]: (modules, no_modules_json)
        """
        from sentence_transformers.util import import_from_string, load_dir_path
        from sentence_transformers.models import Pooling, Normalize

        modules = OrderedDict()
        modules_json_path = FastSentenceTransformer._module_path(model_name, token)

        if modules_json_path:
            with open(modules_json_path, encoding = "utf8") as f:
                modules_config = json.load(f)

            for module_config in modules_config:
                class_ref = module_config["type"]
                name = module_config.get(
                    "name", str(module_config.get("idx", len(modules)))
                )

                if class_ref == "sentence_transformers.models.Transformer":
                    transformer_module = (
                        FastSentenceTransformer._create_transformer_module(
                            model_name,
                            model,
                            tokenizer,
                            max_seq_length,
                            trust_remote_code,
                        )
                    )
                    modules[name] = transformer_module
                else:
                    # load other modules (Pooling, Normalize, etc.)
                    module_path = module_config["path"]
                    if os.path.isdir(model_name):
                        load_path = os.path.join(model_name, module_path)
                    else:
                        try:
                            load_path = load_dir_path(
                                model_name, module_path, token = token
                            )
                        except Exception as e:
                            print(
                                f"Unsloth Warning: Could not download module {module_path}: {e}"
                            )
                            continue

                    module_class = import_from_string(class_ref)
                    try:
                        module = module_class.load(load_path)
                        modules[name] = module
                    except Exception as e:
                        print(
                            f"Unsloth Warning: Failed to load module {name} ({class_ref}): {e}"
                        )

            return modules, False

        # fallback if no modules.json (non sentence-transformers models)
        print(
            "Unsloth: No modules.json found, falling back to [Transformer, Pooling, Normalize]. This may or may not work."
        )

        transformer_module = FastSentenceTransformer._create_transformer_module(
            model_name, model, tokenizer, max_seq_length, trust_remote_code
        )
        modules["0"] = transformer_module

        hidden_size = getattr(model.config, "hidden_size", 768)

        if pooling_mode == "mean":
            pooling_mode = FastSentenceTransformer._read_pooling_mode(model_name, token)

        modules["1"] = Pooling(
            word_embedding_dimension = hidden_size, pooling_mode = pooling_mode
        )
        modules["2"] = Normalize()

        return modules, True
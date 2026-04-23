def patch_saving_functions(model, vision = False):
    import inspect
    import types
    from typing import Callable, Optional, Union, List

    # And now re add our saving methods!
    if model.push_to_hub.__name__ == "unsloth_push_to_hub":
        original_push_to_hub = model.original_push_to_hub
    else:
        original_push_to_hub = model.push_to_hub

    signature = str(inspect.signature(original_push_to_hub)).replace("NoneType", "None")
    signature = signature[1:]
    signature = re.sub("<function save at .+?>", "torch.save", signature)
    docs = original_push_to_hub.__doc__.encode("utf-8").decode("utf-8")

    push_to_hub_text = f'''def unsloth_push_to_hub(self, {signature}:
    """
    {docs}
    """
    arguments = dict(locals())
    del arguments["self"]
    if "tags" in arguments and arguments["tags"] is not None:
        assert(isinstance(arguments["tags"], (list, tuple)))
        arguments["tags"] = list(arguments["tags"]) + ["unsloth",]
    elif "tags" in arguments:
        arguments["tags"] = ["unsloth",]
    elif hasattr(self, "add_model_tags"):
        self.add_model_tags(["unsloth",])

    if "commit_message" in arguments:
        commit_message = arguments["commit_message"]
        if commit_message is not None:
            if not commit_message.endswith(" "): commit_message += " "
            if "Unsloth" not in commit_message:
                commit_message += "(Trained with Unsloth)"
        else:
            commit_message = "Upload model trained with Unsloth"
        arguments["commit_message"] = commit_message

    if "commit_description" in arguments:
        commit_description = arguments["commit_description"]
        if commit_description is not None:
            if not commit_description.endswith(" "): commit_description += " "
            if "Unsloth" not in commit_description:
                commit_description += "(Trained with Unsloth 2x faster)"
        else:
            commit_description = "Upload model trained with Unsloth 2x faster"
        arguments["commit_description"] = commit_description

    # Update model tag
    if hasattr(self, "config"):
        _ = upload_to_huggingface(
            self, arguments["repo_id"], arguments["token"],
            "finetuned", "trl", file_location = None,
            old_username = None, private = arguments["private"],
        )
    pass

    try:
        self.original_push_to_hub(**arguments)
    except:
        del arguments["tags"]
        self.original_push_to_hub(**arguments)
    pass

    if hasattr(self, "config"):
        print("Saved model to https://huggingface.co/" + arguments["repo_id"])
    pass
    '''
    exec(push_to_hub_text, globals())

    def unsloth_tokenizer_save_pretrained(
        self,
        save_directory,
        legacy_format = None,
        filename_prefix = None,
        push_to_hub = False,
        **kwargs,
    ):
        result = self.original_save_pretrained(
            save_directory,
            legacy_format = legacy_format,
            filename_prefix = filename_prefix,
            push_to_hub = False,
            **kwargs,
        )
        _preserve_sentencepiece_tokenizer_assets(
            self,
            save_directory,
            token = kwargs.get("token", None),
        )
        if push_to_hub:
            push_kwargs = dict(kwargs)
            repo_id = push_kwargs.pop("repo_id", save_directory)
            self.push_to_hub(repo_id, **push_kwargs)
        return result

    if (
        isinstance(model, PreTrainedTokenizerBase)
        and model.save_pretrained.__name__ != "unsloth_tokenizer_save_pretrained"
    ):
        model.original_save_pretrained = model.save_pretrained
        model.save_pretrained = types.MethodType(
            unsloth_tokenizer_save_pretrained, model
        )
    elif getattr(model, "tokenizer", None) is not None:
        patch_saving_functions(model.tokenizer)

    original_model = model
    while True:
        # Check if push_to_hub exists before accessing its __name__
        if (
            hasattr(original_model, "push_to_hub")
            and original_model.push_to_hub.__name__ != "unsloth_push_to_hub"
        ):
            original_model.original_push_to_hub = original_model.push_to_hub
            original_model.push_to_hub = types.MethodType(
                unsloth_push_to_hub, original_model
            )
            if hasattr(original_model, "add_model_tags"):
                original_model.add_model_tags(
                    [
                        "unsloth",
                    ]
                )

        if hasattr(original_model, "model"):
            original_model = original_model.model
        else:
            break

    # Add saving methods to top level model
    if not vision:
        if hasattr(model, "config"):
            # Counteract tokenizers
            model.push_to_hub_merged = types.MethodType(
                unsloth_generic_push_to_hub_merged, model
            )
            model.save_pretrained_merged = types.MethodType(
                unsloth_generic_save_pretrained_merged, model
            )
            model.push_to_hub_gguf = types.MethodType(unsloth_push_to_hub_gguf, model)
            model.save_pretrained_gguf = types.MethodType(
                unsloth_save_pretrained_gguf, model
            )
            model.save_pretrained_torchao = types.MethodType(
                unsloth_save_pretrained_torchao, model
            )
            model.push_to_hub_ggml = types.MethodType(
                unsloth_convert_lora_to_ggml_and_push_to_hub, model
            )
            model.save_pretrained_ggml = types.MethodType(
                unsloth_convert_lora_to_ggml_and_save_locally, model
            )
    else:
        # Vision only 1 option
        model.push_to_hub_merged = types.MethodType(
            unsloth_generic_push_to_hub_merged, model
        )
        model.save_pretrained_merged = types.MethodType(
            unsloth_generic_save_pretrained_merged, model
        )
        model.push_to_hub_gguf = types.MethodType(unsloth_push_to_hub_gguf, model)
        model.save_pretrained_gguf = types.MethodType(
            unsloth_save_pretrained_gguf, model
        )
        model.save_pretrained_torchao = types.MethodType(
            unsloth_save_pretrained_torchao, model
        )
    return model
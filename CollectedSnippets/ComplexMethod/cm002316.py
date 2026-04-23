def ignore_undocumented(name: str) -> bool:
    """Rules to determine if `name` should be undocumented (returns `True` if it should not be documented)."""
    # NOT DOCUMENTED ON PURPOSE.
    # Constants uppercase are not documented.
    if name.isupper():
        return True
    # PreTrainedModels / Encoders / Decoders / Layers / Embeddings / Attention are not documented.
    if (
        name.endswith("PreTrainedModel")
        or name.endswith("Decoder")
        or name.endswith("Encoder")
        or name.endswith("Layer")
        or name.endswith("Embeddings")
        or name.endswith("Attention")
    ):
        return True
    # Submodules are not documented.
    if os.path.isdir(os.path.join(PATH_TO_TRANSFORMERS, name)) or os.path.isfile(
        os.path.join(PATH_TO_TRANSFORMERS, f"{name}.py")
    ):
        return True
    # All load functions are not documented.
    if name.startswith("load_pytorch"):
        return True
    # is_xxx_available functions are not documented.
    if name.startswith("is_") and name.endswith("_available"):
        return True
    # Deprecated objects are not documented.
    if name in DEPRECATED_OBJECTS or name in UNDOCUMENTED_OBJECTS:
        return True
    # MMBT model does not really work.
    if name.startswith("MMBT"):
        return True
    # BLT models are internal building blocks, tested implicitly through BltForCausalLM
    if name.startswith("Blt"):
        return True
    # image_processing_*_fast are backward-compat module aliases, not public objects.
    if name.startswith("image_processing_") and name.endswith("_fast"):
        return True
    if name in SHOULD_HAVE_THEIR_OWN_PAGE:
        return True
    return False
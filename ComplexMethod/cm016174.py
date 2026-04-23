def compile_model(model, mode, block_types, backend="inductor"):
    if mode == "full":
        model.compile(backend=backend, fullgraph=True, mode="reduce-overhead")
    elif mode == "regional":
        for submod in model.modules():
            if isinstance(submod, block_types):
                print("Compiling", submod.__class__)
                submod.compile(backend=backend, fullgraph=True)
    elif mode == "hierarchical":
        for submod in model.modules():
            if isinstance(submod, block_types):
                submod.__class__.forward = mark_compile_region(submod.__class__.forward)
        model.compile(backend=backend, fullgraph=True)
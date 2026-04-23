def _preserve_emap_position(model, numpy_helper):
    """Keep the insightface emap (512×512 matrix) as the last initializer."""
    graph = model.graph
    emap_init = None
    for init in graph.initializer:
        if not init.name.startswith("_rp_"):
            arr = numpy_helper.to_array(init)
            if len(arr.shape) == 2 and arr.shape[0] == 512 and arr.shape[1] == 512:
                emap_init = init
                break

    if emap_init is not None:
        inits = [i for i in graph.initializer if i.name != emap_init.name]
        del graph.initializer[:]
        graph.initializer.extend(inits)
        graph.initializer.append(emap_init)
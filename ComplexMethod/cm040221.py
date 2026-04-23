def get_attr_skipset(obj_type):
    skipset = global_state.get_global_attribute(
        f"saving_attr_skiplist_{obj_type}", None
    )
    if skipset is not None:
        return skipset

    skipset = set(
        [
            "_self_unconditional_dependency_names",
        ]
    )
    if obj_type == "Operation":
        from keras.src.ops.operation import Operation

        ref_obj = Operation()
        skipset.update(dir(ref_obj))
    elif obj_type == "Layer":
        from keras.src.layers.layer import Layer

        ref_obj = Layer()
        skipset.update(dir(ref_obj))
    elif obj_type == "Functional":
        from keras.src.layers.layer import Layer

        ref_obj = Layer()
        skipset.update(dir(ref_obj) + ["operations", "_operations"])
    elif obj_type == "Sequential":
        from keras.src.layers.layer import Layer

        ref_obj = Layer()
        skipset.update(dir(ref_obj) + ["_functional"])
    elif obj_type == "Metric":
        from keras.src.metrics.metric import Metric
        from keras.src.trainers.compile_utils import CompileMetrics

        ref_obj_a = Metric()
        ref_obj_b = CompileMetrics([], [])
        skipset.update(dir(ref_obj_a) + dir(ref_obj_b))
    elif obj_type == "Optimizer":
        from keras.src.optimizers.optimizer import Optimizer

        ref_obj = Optimizer(1.0)
        skipset.update(dir(ref_obj))
        skipset.remove("variables")
    elif obj_type == "Loss":
        from keras.src.losses.loss import Loss

        ref_obj = Loss()
        skipset.update(dir(ref_obj))
    elif obj_type == "Cross":
        from keras.src.layers.preprocessing.feature_space import Cross

        ref_obj = Cross((), 1)
        skipset.update(dir(ref_obj))
    elif obj_type == "Feature":
        from keras.src.layers.preprocessing.feature_space import Feature

        ref_obj = Feature("int32", lambda x: x, "int")
        skipset.update(dir(ref_obj))
    else:
        raise ValueError(
            f"get_attr_skipset got invalid {obj_type=}. "
            "Accepted values for `obj_type` are "
            "['Operation', 'Layer', 'Functional', 'Sequential', 'Metric', "
            "'Optimizer', 'Loss', 'Cross', 'Feature']"
        )

    global_state.set_global_attribute(
        f"saving_attr_skipset_{obj_type}", skipset
    )
    return skipset
def get_weight_spec_of_saveable(saveable, spec, visited_saveables=None):
    from keras.src.saving.keras_saveable import KerasSaveable

    visited_saveables = visited_saveables or set()

    # If the saveable has already been saved, skip it.
    if id(saveable) in visited_saveables:
        return

    if hasattr(saveable, "save_own_variables"):
        store = {}
        saveable.save_own_variables(store)
        if store:
            keys = sorted(store.keys())
            for k in keys:
                val = store[k]
                spec[k] = backend.KerasTensor(shape=val.shape, dtype=val.dtype)

    visited_saveables.add(id(saveable))

    for child_attr, child_obj in saving_lib._walk_saveable(saveable):
        if isinstance(child_obj, KerasSaveable):
            sub_spec = {}
            get_weight_spec_of_saveable(
                child_obj,
                sub_spec,
                visited_saveables=visited_saveables,
            )
            if sub_spec:
                spec[child_attr] = sub_spec
        elif isinstance(child_obj, (list, dict, tuple, set)):
            sub_spec = {}
            get_weight_spec_of_container(
                child_obj,
                sub_spec,
                visited_saveables=visited_saveables,
            )
            if sub_spec:
                spec[child_attr] = sub_spec
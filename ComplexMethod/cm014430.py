def _list_connected_datapipes(
    scan_obj: DataPipe, only_datapipe: bool, cache: set[int]
) -> list[DataPipe]:
    f = io.BytesIO()
    p = pickle.Pickler(
        f
    )  # Not going to work for lambdas, but dill infinite loops on typing and can't be used as is
    if dill_available():
        from dill import Pickler as dill_Pickler

        d = dill_Pickler(f)
    else:
        d = None

    captured_connections = []

    def getstate_hook(ori_state):
        state = None
        if isinstance(ori_state, dict):
            state = {}
            for k, v in ori_state.items():
                if isinstance(v, (IterDataPipe, MapDataPipe, Collection)):
                    state[k] = v
        elif isinstance(ori_state, (tuple, list)):
            state = []  # type: ignore[assignment]
            for v in ori_state:
                if isinstance(v, (IterDataPipe, MapDataPipe, Collection)):
                    state.append(v)  # type: ignore[attr-defined]
        elif isinstance(ori_state, (IterDataPipe, MapDataPipe, Collection)):
            state = ori_state  # type: ignore[assignment]
        return state

    def reduce_hook(obj):
        if obj == scan_obj or id(obj) in cache:
            raise NotImplementedError
        else:
            captured_connections.append(obj)
            # Adding id to remove duplicate DataPipe serialized at the same level
            cache.add(id(obj))
            return _stub_unpickler, ()

    datapipe_classes: tuple[type[DataPipe]] = (IterDataPipe, MapDataPipe)  # type: ignore[assignment]

    try:
        for cls in datapipe_classes:
            cls.set_reduce_ex_hook(reduce_hook)
            if only_datapipe:
                cls.set_getstate_hook(getstate_hook)
        try:
            p.dump(scan_obj)
        except (pickle.PickleError, AttributeError, TypeError):
            if dill_available():
                # pyrefly: ignore [missing-attribute]
                d.dump(scan_obj)
            else:
                raise
    finally:
        for cls in datapipe_classes:
            cls.set_reduce_ex_hook(None)
            if only_datapipe:
                cls.set_getstate_hook(None)
        if dill_available():
            from dill import extend as dill_extend

            dill_extend(False)  # Undo change to dispatch table
    return captured_connections
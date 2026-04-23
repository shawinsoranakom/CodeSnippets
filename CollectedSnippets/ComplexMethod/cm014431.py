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
def _check_on_train_epoch_start(self, pl_module, callback):
        """Basically ensures that the sparsifier's state is correctly being restored.
        The state_dict() comparison is needed. Consider the flow -

        **Epoch: 1**
            1. on_train_epoch_start(): Nothing happens (for now)
            2. on_train_epoch_end():
                a) the model is copied into the data_sparsifier
                b) .step() is called
                c) internally, the state of each layer of the model inside
                   data sparsifier changes

        **Epoch: 2**
            1. on_train_epoch_start(): Assume nothing happens
            2. on_train_epoch_end():
                a) the model is copied into the data_sparsifier.
                   But wait! you need the config to attach layer
                   of the module to the sparsifier. If config is None,
                   the data_sparsifier uses the default config which we
                   do not want as the config of each layer changes after
                   .step()

        Hence, we need to dump and restore the state_dict() every time because we're
        copying the model after each epoch.
        Hence, it is essential to make sure that the sparsifier's state_dict() is being
        correctly dumped and restored.

        """
        # check if each component of state dict is being loaded correctly
        callback.on_train_epoch_start(42, pl_module)
        if callback.data_sparsifier_state_dict is None:
            return

        data_sparsifier_state_dict = callback.data_sparsifier.state_dict()

        # compare container objects
        container_obj1 = data_sparsifier_state_dict["_container"]
        container_obj2 = callback.data_sparsifier_state_dict["_container"]
        if len(container_obj1) != len(container_obj2):
            raise AssertionError(
                f"container lengths differ: {len(container_obj1)} vs {len(container_obj2)}"
            )
        for key, value in container_obj2.items():
            if key not in container_obj1:
                raise AssertionError(f"key {key!r} not in container_obj1")
            if not torch.all(value == container_obj1[key]):
                raise AssertionError(f"container values differ for key {key!r}")

        # compare state objects
        state_obj1 = data_sparsifier_state_dict["state"]
        state_obj2 = callback.data_sparsifier_state_dict["state"]
        if len(state_obj1) != len(state_obj2):
            raise AssertionError(
                f"state lengths differ: {len(state_obj1)} vs {len(state_obj2)}"
            )
        for key, value in state_obj2.items():
            if key not in state_obj1:
                raise AssertionError(f"key {key!r} not in state_obj1")
            if not ("mask" in value and "mask" in state_obj1[key]):
                raise AssertionError(f"'mask' not in value or state_obj1[{key!r}]")
            if not torch.all(value["mask"] == state_obj1[key]["mask"]):
                raise AssertionError(f"mask values differ for key {key!r}")

        # compare data_groups dict
        data_grp1 = data_sparsifier_state_dict["data_groups"]
        data_grp2 = callback.data_sparsifier_state_dict["data_groups"]
        if len(data_grp1) != len(data_grp2):
            raise AssertionError(
                f"data_groups lengths differ: {len(data_grp1)} vs {len(data_grp2)}"
            )
        for key, value in data_grp2.items():
            if key not in data_grp1:
                raise AssertionError(f"key {key!r} not in data_grp1")
            if value != data_grp1[key]:
                raise AssertionError(
                    f"data_groups[{key!r}] differ: {value} vs {data_grp1[key]}"
                )
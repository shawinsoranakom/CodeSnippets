def _build_fully_connected(
            self,
            inputs: dict[str, keras.models.Model]) -> dict[str, list[keras.models.Model]]:
        """ Build the fully connected layers for Phaze-A

        Parameters
        ----------
        inputs: dict
            The compiled encoder models that act as inputs to the fully connected layers

        Returns
        -------
        dict
            side as key ('a' or 'b'), fully connected model for side as value
        """
        input_shapes = inputs["a"].shape[1:]

        fc_a = fc_both = None
        if cfg.split_fc():
            fc_a = FullyConnected("a", input_shapes)()
            inter_a = [fc_a(inputs["a"])]
            inter_b = [FullyConnected("b", input_shapes)()(inputs["b"])]
        else:
            fc_both = FullyConnected("both", input_shapes)()
            inter_a = [fc_both(inputs["a"])]
            inter_b = [fc_both(inputs["b"])]

        shared_fc = None if cfg.shared_fc() == "none" else cfg.shared_fc()
        if shared_fc:
            if shared_fc == "full":
                fc_shared = FullyConnected("shared", input_shapes)()
            elif cfg.split_fc():
                assert fc_a is not None
                fc_shared = fc_a
            else:
                assert fc_both is not None
                fc_shared = fc_both
            inter_a = [kl.Concatenate(name="inter_a")([inter_a[0], fc_shared(inputs["a"])])]
            inter_b = [kl.Concatenate(name="inter_b")([inter_b[0], fc_shared(inputs["b"])])]

        if cfg.enable_gblock():
            fc_gblock = FullyConnected("gblock", input_shapes)()
            inter_a.append(fc_gblock(inputs["a"]))
            inter_b.append(fc_gblock(inputs["b"]))

        inter_a = inter_a[0] if len(inter_a) == 1 else inter_a
        inter_b = inter_b[0] if len(inter_b) == 1 else inter_b
        retval = {"a": inter_a, "b": inter_b}
        logger.debug("Fully Connected: %s", retval)
        return retval
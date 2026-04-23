def decide_layout_opt(gm: GraphModule, *, is_inference: bool) -> bool:
        """
        Decide if we should enable layout optimization for this graph based on
        heuristics.
        """
        if not config.layout_optimization:
            return False

        if config.force_layout_optimization:
            return True

        conv_nodes = [
            n for n in gm.graph.nodes if n.target is torch.ops.aten.convolution.default
        ]

        for n in gm.graph.nodes:
            if is_mkldnn_conv(n):
                conv_nodes.append(n)

        nconv = len(conv_nodes)

        if nconv == 0:
            return False

        # For cpu backend and mkldnn enabled, we always use channels_last for better performance.
        if (
            torch.backends.mkldnn.enabled  # pyrefly: ignore [unbound-name]
            and torch.backends.mkldnn.is_available()  # pyrefly: ignore [unbound-name]
            and all(
                n.args[idx].meta["val"].device.type in SUPPORTED_MKLDNN_DEVICES
                for n in conv_nodes
                for idx in [0, 1]
            )
        ):
            return True

        # Following models are skipped due to this:
        # jx_nest_base
        # volo_d1_224
        if len(list(gm.graph.nodes)) >= 300 * nconv:
            log.debug("Skipped layout opt because only a few conv")
            return False

        if any(
            has_free_symbols(n.args[idx].meta["val"])
            for n in conv_nodes
            for idx in [0, 1]
        ):
            log.debug(
                "See perf regression with dynamic shape. Follow up in https://github.com/pytorch/pytorch/issues/102670"
            )
            return False

        def is_grouped(n: Any) -> bool:
            meta_val = n.args[1].meta["val"]  # type: ignore[union-attr, operator]
            assert isinstance(meta_val, torch.Tensor)
            return n.args[-1] > 1 and meta_val.size(1) > 1  # type: ignore[union-attr, operator]

        def is_in_out_channel(n: torch.fx.Node) -> bool:
            return (
                n.args[1].meta["val"].size(0) * 2 <= n.args[1].meta["val"].size(1)  # type: ignore[union-attr, operator]
                and n.args[1].meta["val"].size(2) > 1  # type: ignore[union-attr, operator]
            )

        def is_small_channel(n: torch.fx.Node) -> bool:
            return (
                n.args[1].meta["val"].size(0) <= 64  # type: ignore[union-attr, operator]
                and n.args[1].meta["val"].size(1) <= 64  # type: ignore[union-attr, operator]
            )

        # only grouped convolutions benchmarked as slower in conv samples for inference only
        if is_inference:
            flop_counts: dict[str, float] = defaultdict(float)
            for node in conv_nodes:
                counted_flops = count_flops_fx(node)
                if counted_flops is None:
                    continue

                if is_grouped(node):
                    node_type = "grouped"
                elif is_small_channel(node):
                    node_type = "small"
                elif is_in_out_channel(node):
                    node_type = "in_out"
                else:
                    node_type = "default"

                flop_counts[node_type] += counted_flops
            else:
                log.debug("Conv inputs meta not found")

            # average benchmarked channels last speedup / slowdown, < 1 is speedup.
            # taken from the set of convolution inputs in benchmarks/dynamo/microbenchmarks/operator_inp_logs/torchbench_train/
            # To regenerate these numbers follow https://gist.github.com/eellison/55d7a6ed6f39829d68ac56f95f4df5bb
            GROUPED_MULTIPLIER = 1.358
            DEFAULT_MULTIPLIER = 0.823
            IN_OUT_MULTIPLIER = 0.725
            SMALL_MULTIPLIER = 0.783

            total_flops = sum(flop_counts.values())
            # TODO - get different values per hardware
            weighted_flops = (
                flop_counts["grouped"] * GROUPED_MULTIPLIER
                + flop_counts["small"] * SMALL_MULTIPLIER
                + flop_counts["in_out"] * IN_OUT_MULTIPLIER
                + flop_counts["default"] * DEFAULT_MULTIPLIER
            )
            do_layout_opt = weighted_flops <= total_flops
            if not do_layout_opt:
                log.debug(
                    "Skipped layout opt in inference because weighted flops indicate slowdown, default: %d, channels last: %d",
                    total_flops,
                    weighted_flops,
                )
            return do_layout_opt

        # Channels last layout can dramatically hurt grouped conv perf. E.g.
        # Conv with arguments like
        #   {"input_shape": [32, 224, 112, 112], "weight_shape": [224, 112, 3, 3],
        #    "stride": [2, 2], "padding": [1, 1], "groups": 2}
        # slows down 31x using channels last..

        # But a lot of timm models use depthwise separable convolution which will
        # result in grouped convolution with in-channel size == 1.
        # For those grouped convolution, channels last still helps a lot.
        # E.g.
        # Conv with arguments
        #   {"input_shape": [128, 58, 56, 56], "weight_shape": [58, 1, 3, 3],
        #    "stride": [2, 2], "padding": [1, 1], "groups": 58}
        # get 1.86x speedup with channels last layout.
        #
        # The following heuristics skip using channels-last if the model contains
        # grouped convolution with in-channels > 1.
        if any(map(is_grouped, conv_nodes)):
            log.debug(
                "Skip layout opt because found grouped convolution with >1 in_channels!"
            )
            return False

        # For some models that contain convolution with larger in-channel than out-channel, applying
        # channels last hurts performance.
        # Following models are skipped due to this:
        # - pytorch_unet
        # - phlippe_densenet (slightly worse)
        # - Background_Matting (1.22x -> 0.821x)
        # - pytorch_CycleGAN_and_pix2pix (1.597x -> 1.294x)
        if any(map(is_in_out_channel, conv_nodes)):
            log.debug(
                "Skip layout opt because some convolutions have smaller out_channel"
            )
            return False

        # Following models are skipped due to this:
        # - functorch_maml_omniglot
        if all(map(is_small_channel, conv_nodes)):
            log.debug("Skip layout opt because all convolution channels are too small")
            return False

        return True
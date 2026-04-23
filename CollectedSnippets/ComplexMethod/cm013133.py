def checkGraphModeOp(
        self,
        module,
        inputs,
        quantized_op,
        tracing=False,
        debug=False,
        check=True,
        eval_mode=True,
        dynamic=False,
        qconfig=None,
    ):
        if debug:
            print("Testing:", str(module))
        qconfig_dict = {"": get_default_qconfig(torch.backends.quantized.engine)}

        if eval_mode:
            module = module.eval()
        if dynamic:
            qconfig_dict = {"": default_dynamic_qconfig if qconfig is None else qconfig}
        model = get_script_module(module, tracing, inputs[0]).eval()
        if debug:
            print("input graph:", model.graph)
        models = {}
        outputs = {}
        for debug in [True, False]:
            if dynamic:
                models[debug] = quantize_dynamic_jit(model, qconfig_dict, debug=debug)
                # make sure it runs
                outputs[debug] = models[debug](inputs)
            else:
                # module under test can contain in-place ops, and we depend on
                # input data staying constant for comparisons
                inputs_copy = copy.deepcopy(inputs)
                models[debug] = quantize_jit(
                    model,
                    qconfig_dict,
                    test_only_eval_fn,
                    [inputs_copy],
                    inplace=False,
                    debug=debug,
                )
                # make sure it runs
                outputs[debug] = models[debug](*inputs[0])

        if debug:
            print("debug graph:", models[True].graph)
            print("non debug graph:", models[False].graph)

        if check:
            # debug and non-debug option should have the same numerics
            self.assertEqual(outputs[True], outputs[False])

            # non debug graph should produce quantized op
            FileCheck().check(quantized_op).run(models[False].graph)

        return models[False]
def _build_test(
    configs, bench_op, OperatorTestCase, run_backward, op_name_function=None
):
    """Generate PyTorch/Caffe2 tests of operators with different inputs.
    Args:
        configs: a dictionary that has the input shapes
        bench_op: a subclass of TorchBenchmarkBase which includes tensor
            creation and operator execution
        OperatorTestCase: a named tuple to save the metadata of an test
        run_backward: a bool parameter indicating backward path
        op_name_function: a dictionary includes operator name and function
    """
    for config in configs:
        test_attrs = {}
        tags = None
        keep_config = True
        for attr in config:
            # tags is only used in our benchmark backend to filter tests and
            # it will be removed from config which is then passed to the init function
            # an example of config and atrr is:
            # config: [{'M': 16}, {'N': 16}, {'K': 64}, {'tags': 'short'}]
            # attr: {'tags': 'short'}
            if "tags" in attr:
                tags = attr["tags"]
                continue

            # if 'cuda' is specified in input shape but the testing machines doesn't
            # support, we will skip this input
            if "cuda" in attr.values():
                if not torch.cuda.is_available():
                    keep_config = False
                    break

            test_attrs.update(attr)

        if not keep_config:
            continue

        if tags is None:
            raise ValueError("Missing tags in configs")

        op = bench_op()
        if op is None:
            raise AssertionError("Can't create test: bench_op() returned None")
        # op_name_function is a dictionary which has op_name and op_function.
        # an example of op_name_function is:
        # {'op_name' : 'abs', 'op_function' : torch.abs}
        # op_function is concatenated with the input dict then passed to the init function
        # op_name is passed to the set_module_name function
        init_dict = copy.deepcopy(test_attrs)
        if op_name_function is not None:
            op_name = op_name_function["op_name"]
            init_dict.update({"op_func": op_name_function["op_func"]})
            op.set_module_name(op_name)

        op._set_backward_test(run_backward)
        op.init(**init_dict)
        op.extract_inputs_tuple()

        if not run_backward:
            for attr in vars(op).values():
                if isinstance(attr, torch.nn.Module):
                    for param in attr.parameters():
                        param.requires_grad = False

        input_name = None

        # _num_inputs_require_grads is used to track the number of tensors
        # which use auto_set().
        if op._num_inputs_require_grads > 0:
            input_name = "all"
        yield _create_test(
            op, test_attrs, tags, OperatorTestCase, run_backward, input_name
        )

        # This for loop is only used when auto_set is used.
        # _pass_count counts how many times init has been called.
        # _auto_set_counter is reset after init is called.
        for i in range(op._num_inputs_require_grads):
            op._pass_count += 1
            op._auto_set_counter = 0

            # TODO(mingzhe09088): remove this deepcopy when we encounter
            # performance issue.
            new_op = copy.deepcopy(op)
            new_op.init(**init_dict)
            # Input name index will start from input1
            input_name = i + 1
            yield _create_test(
                new_op, test_attrs, tags, OperatorTestCase, run_backward, input_name
            )
def _test_model_impl(
            self, mode, name, model, eager_quantizable_model,
            check_with_eager=True,
            diff_of_quant=None,
            diff_from_eager=None):
        if diff_of_quant is None or diff_from_eager is None:
            diff_of_quant = {}
            diff_from_eager = {}

        if mode not in diff_of_quant or mode not in diff_from_eager:
            diff_of_quant[mode] = {}
            diff_from_eager[mode] = {}

        input_tensor = torch.rand(1, 3, 224, 224)
        input_tensor_inception = torch.rand(1, 3, 299, 299)
        output_value = torch.randint(0, 1, (1,))

        # print('quantizing:', name, ' mode:', mode)
        if name == 'inception_v3':
            input_value = input_tensor_inception
        else:
            input_value = input_tensor

        qconfig = default_qconfig if mode == 'static' else default_qat_qconfig
        qconfig_dict = {'': qconfig}
        script = torch.jit.script(model)

        # make sure graph module and script module are both runanble
        original_out = model(input_value)
        is_not_tuple_out = not isinstance(original_out, tuple)
        script_out = script(input_value)

        # set to train just before quantization
        prepare_fx_fn = prepare_fx
        if mode != 'static':
            model.train()
            prepare_fx_fn = prepare_qat_fx

        prepared = prepare_fx_fn(model, qconfig_dict)

        if mode == 'ddp':
            mp.spawn(run_ddp,
                     args=(world_size, prepared),  # noqa: F821
                     nprocs=world_size,  # noqa: F821
                     join=True)
        elif mode == 'qat':
            if not prepared.training:
                raise AssertionError("prepared must be in training mode for qat")
            optimizer = torch.optim.SGD(prepared.parameters(), lr=0.0001)
            criterion = nn.CrossEntropyLoss()
            train_one_epoch(prepared, criterion, optimizer, [(input_value, output_value)], torch.device('cpu'), 1)
        else:
            for _ in range(10):
                prepared(input_value)

        # print('after observation root:', prepared.root)

        qgraph = convert_fx(prepared)
        # print('after quantization root:', qgraph.root)
        # print('after quantization code:', qgraph.src)
        qgraph.eval()
        qgraph_script = torch.jit.script(qgraph)
        # print('quantized and scripted:', qgraph_script.graph)

        qgraph_out = qgraph(input_value)
        qgraph_script = qgraph_script(input_value)

        if is_not_tuple_out:
            diff_of_quant[mode][name] = (original_out - qgraph_out).abs().max()
            if not torch.allclose(qgraph_out, qgraph_script):
                raise AssertionError("graph, scripted graph")
        else:
            print('tuple output')

        if eager_quantizable_model is not None:
            # comparing to eager mode quantization
            qeager = eager_quantizable_model
            ref_out = qeager(input_value)
            qeager.qconfig = qconfig
            if mode == 'static':
                qeager.fuse_model()
                prepare(qeager, inplace=True)
            else:
                qeager.train()
                qeager.fuse_model()
                prepare_qat(qeager, inplace=True)

            # calibration
            if mode == 'ddp':
                mp.spawn(run_ddp,
                         args=(world_size, qeager),  # noqa: F821
                         nprocs=world_size,  # noqa: F821
                         join=True)
            elif mode == 'qat':
                if not qeager.training:
                    raise AssertionError("qeager should be in training mode for qat")
                optimizer = torch.optim.SGD(qeager.parameters(), lr=0.0001)
                train_one_epoch(qeager, criterion, optimizer, [(input_value, output_value)], torch.device('cpu'), 1)
            else:
                for _ in range(10):
                    qeager(input_value)

            # print('ref after observation:', qeager)

            convert(qeager, inplace=True)
            qeager.eval()

            # print('ref after quantization:', qeager)
            qeager_out = qeager(input_value)
            qeager_script = torch.jit.script(qeager)
            qscript_out = qeager_script(input_value)
            if is_not_tuple_out:
                diff_from_eager[mode][name] = (qeager_out - qgraph_out).abs().max()
                if check_with_eager:
                    self.assertEqual(diff_from_eager[mode][name], 0,
                                     'Result of graph mode quantization and ' +
                                     'eager mode quantization on model: ' + name +
                                     ' should match. Mode: ' + mode +
                                     ' diff:' + str(diff_from_eager[mode][name]))
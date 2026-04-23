def _test_ddp_multiple_nested_unused_params_error(self, ignore_sparse):
            debug_mode_off = dist.get_debug_level() == dist.DebugLevel.OFF

            class SubModule(nn.Module):
                def __init__(self) -> None:
                    super().__init__()
                    self.embedding_net = EmbeddingNetDifferentParams(0)
                    self.lin = TwoLinLayerNet()
                    self.bn = BatchNormNet()
                    self.lin_layer = nn.Linear(4, 10, bias=False)

                def forward(self, x):
                    x = self.bn(x)
                    x = self.lin_layer(x)
                    x = self.lin.a(x)  # self.lin.b param unused
                    # EmbeddingNetDifferentParams entirely unused: self.embedding_net.embedding and
                    # self.embedding_net.lin unused.
                    return x

            class MyModel(nn.Module):
                def __init__(self) -> None:
                    super().__init__()
                    self.sub_module = SubModule()

                def forward(self, x):
                    return self.sub_module(x)

            model = MyModel()
            sparse_embedding_fqns = []
            if ignore_sparse:
                for module_name, module in model.named_modules():
                    if module == model.sub_module.embedding_net.embedding:
                        for parameter_name, _param in module.named_parameters(
                            recurse=False
                        ):
                            fqn = f"{module_name}.{parameter_name}"
                            sparse_embedding_fqns.append(fqn)

                torch.nn.parallel.DistributedDataParallel._set_params_and_buffers_to_ignore_for_model(
                    model, sparse_embedding_fqns
                )
                unused_modules = [
                    model.sub_module.embedding_net.lin,
                    model.sub_module.lin.b,
                ]
            else:
                unused_modules = list(model.sub_module.embedding_net.modules()) + [
                    model.sub_module.lin.b,
                ]

            expected_unused_param_fqns = []
            used_param_fqns = []  # Validate that these don't mistakenly show up.
            fqn_to_param_index = {}
            index = 0
            for module_name, module in model.named_modules():
                for parameter_name, _param in module.named_parameters(recurse=False):
                    fqn = f"{module_name}.{parameter_name}"
                    fqn_to_param_index[fqn] = index
                    if fqn not in sparse_embedding_fqns:
                        index += 1
                    if module in unused_modules:
                        expected_unused_param_fqns.append(fqn)
                    else:
                        if (
                            not ignore_sparse
                            or module != model.sub_module.embedding_net.embedding
                        ):
                            used_param_fqns.append(fqn)

            net = torch.nn.parallel.DistributedDataParallel(
                model.cuda(self.rank),
                device_ids=[self.rank],
            )
            batch, dim = 10, 2
            inp = torch.ones(batch, dim)
            for i in range(2):
                if i == 0:
                    out = net(inp)
                    loss = out.sum()
                    loss.backward()
                else:
                    try:
                        out = net(inp)
                        loss = out.sum()
                        loss.backward()
                    except RuntimeError as e:
                        e = str(e)

                        unused_param_substr = e[e.find("did not receive grad") :]
                        # Validate that each unused param fully qualified name
                        # shows up in error logs. We do this instead of
                        # constructing a joined string since order of parameters
                        # can be different in Reducer. In addition, validate
                        # param indices show up as well.
                        for unused_param_fqn in expected_unused_param_fqns:
                            self.assertTrue(
                                unused_param_fqn in unused_param_substr
                                or debug_mode_off
                            )
                            self.assertTrue(
                                str(fqn_to_param_index[unused_param_fqn])
                                in unused_param_substr,
                                f"Did not find index {fqn_to_param_index[unused_param_fqn]} for {unused_param_fqn}",
                            )

                        # Validate that used param fqns don't show up in error
                        # logs.
                        for used_param_fqn in used_param_fqns:
                            self.assertFalse(used_param_fqn in unused_param_substr)
                        # Validate that ignored param fqns don't show up as unused
                        # (since DDP does not track them)
                        for sparse_param_fqn in sparse_embedding_fqns:
                            self.assertFalse(sparse_param_fqn in unused_param_substr)
                    else:
                        self.assertTrue(False, "Expected error was not raised!")
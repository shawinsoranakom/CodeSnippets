def _get_lstm_with_individually_observed_parts(
    float_lstm: torch.nn.LSTM,
    example_inputs: tuple[Any, ...],
    backend_config: BackendConfig | None = None,
    linear_output_obs_ctr: _PartialWrapper | None = None,
    sigmoid_obs_ctr: _PartialWrapper | None = None,
    tanh_obs_ctr: _PartialWrapper | None = None,
    cell_state_obs_ctr: _PartialWrapper | None = None,
    hidden_state_obs_ctr: _PartialWrapper | None = None,
    split_gates: bool = False,
) -> torch.ao.nn.quantizable.LSTM:
    """
    Return an observed `torch.ao.nn.quantizable.LSTM` created from a `torch.nn.LSTM`
    with specific observers or fake quantizes assigned to the inner ops or submodules.

    In both eager and FX graph mode quantization, `torch.ao.nn.quantizable.LSTM` is
    used as an observed custom module, which is responsible for inserting its own
    observers. By default, all inner ops inherit the parent custom module's QConfig.
    Users who wish to override this behavior may extend `torch.ao.nn.quantizable.LSTM`
    and use this helper function to customize the observer insertion logic.

    This is meant to be used to convert a float module to an observed module in the
    custom module flow.

    Args:
        `float_lstm`: The float LSTM module
        `example_inputs`: example inputs for the forward function of the LSTM module
        `backend_config`: BackendConfig to use to observe the LSTM module
        `linear_output_obs_ctr`: observer or fake quantize for linear outputs Wx + b,
            where W is the weight matrix, b is the bias, and x is either the inputs
            or the hidden state from the previous layer (if any)
        `sigmoid_obs_ctr`: observer or fake quantize for sigmoid activations
        `tanh_obs_ctr`: observer or fake quantize for tanh activations
        `cell_state_obs_ctr`: observer or fake quantize for the cell state
        `hidden_state_obs_ctr`: observer or fake quantize for the hidden state and
            the output

    Return:
        A `torch.ao.nn.quantizable.LSTM` with the specified observers or fake quantizes
        assigned to the inner ops.
    """

    def make_qconfig(obs_ctr: _PartialWrapper) -> QConfig:
        """
        Make a QConfig with fixed qparams observers or fake quantizes.
        """
        if isinstance(obs_ctr(), FakeQuantizeBase):
            weight = default_weight_fake_quant
        else:
            weight = default_weight_observer
        return QConfig(activation=obs_ctr, weight=weight)

    quantizable_lstm = torch.ao.nn.quantizable.LSTM(
        float_lstm.input_size,
        float_lstm.hidden_size,
        float_lstm.num_layers,
        float_lstm.bias,
        float_lstm.batch_first,
        float_lstm.dropout,
        float_lstm.bidirectional,
        split_gates=split_gates,
    )
    quantizable_lstm.qconfig = float_lstm.qconfig

    for idx in range(float_lstm.num_layers):
        quantizable_lstm.layers[idx] = (
            torch.ao.nn.quantizable.modules.rnn._LSTMLayer.from_float(
                float_lstm,
                idx,
                float_lstm.qconfig,
                batch_first=False,
                split_gates=split_gates,
            )
        )

    # Build QConfigMapping for the LSTM cell
    # Note: FloatFunctional qconfigs will be configured separately below
    cell_qm = QConfigMapping().set_global(float_lstm.qconfig)  # type: ignore[arg-type]
    if sigmoid_obs_ctr is not None:
        cell_qm.set_module_name("input_gate", make_qconfig(sigmoid_obs_ctr))
        cell_qm.set_module_name("forget_gate", make_qconfig(sigmoid_obs_ctr))
        cell_qm.set_module_name("output_gate", make_qconfig(sigmoid_obs_ctr))
    if tanh_obs_ctr is not None:
        cell_qm.set_module_name("cell_gate", make_qconfig(tanh_obs_ctr))

    # Insert observers into each LSTM cell
    # TODO: maybe make this work for layer_bw as well
    for layer in quantizable_lstm.layers:
        cell = layer.layer_fw.cell  # type: ignore[union-attr]
        if not isinstance(cell, torch.nn.Module):
            raise AssertionError("cell should be a nn.Module")
        cell = prepare_fx(cell, cell_qm, example_inputs, backend_config=backend_config)
        # HACK: Manually replace the activation_post_process following these ops.
        # This is needed for FloatFunctional ops because there is currently no way
        # to configure these ops in FX graph mode quantization today. This is because
        # the FloatFunctional modules simply disappear from the graph after tracing.
        # In the future, we should rewrite quantizable LSTM without FloatFunctionals.
        if not split_gates:
            op_index_to_activation_post_process_ctr = {
                (torch.add, 0): linear_output_obs_ctr,  # gates.add
                (torch.mul, 0): cell_state_obs_ctr,  # fgate_cx.mul
                (torch.mul, 1): cell_state_obs_ctr,  # igate_cgate.mul
                (torch.add, 1): cell_state_obs_ctr,  # fgate_cx_igate_cgate.add
                (torch.mul, 2): hidden_state_obs_ctr,  # ogate_cy.mul
            }
        else:
            op_index_to_activation_post_process_ctr = {
                (torch.add, 0): linear_output_obs_ctr,  # gates.add (input)
                (torch.add, 1): linear_output_obs_ctr,  # gates.add (forget)
                (torch.add, 2): linear_output_obs_ctr,  # gates.add (cell)
                (torch.add, 3): linear_output_obs_ctr,  # gates.add (output)
                (torch.mul, 0): cell_state_obs_ctr,  # fgate_cx.mul
                (torch.mul, 1): cell_state_obs_ctr,  # igate_cgate.mul
                (torch.add, 4): cell_state_obs_ctr,  # fgate_cx_igate_cgate.add
                (torch.mul, 2): hidden_state_obs_ctr,  # ogate_cy.mul
            }
        add_count = 0
        mul_count = 0
        for node in cell.graph.nodes:
            op_index: tuple[Callable, int] | None = None  # e.g. (torch.add, 1)
            if node.target is torch.add:
                op_index = (torch.add, add_count)
                add_count += 1
            elif node.target is torch.mul:
                op_index = (torch.mul, mul_count)
                mul_count += 1
            else:
                # Neither torch.add nor torch.mul
                continue
            if op_index not in op_index_to_activation_post_process_ctr:
                continue
            if len(node.users) != 1:
                raise AssertionError("expected exactly one user for the node")
            activation_post_process_name = next(iter(node.users.keys())).name
            activation_post_process_ctr = op_index_to_activation_post_process_ctr[
                op_index
            ]
            if activation_post_process_ctr is not None:
                setattr(
                    cell, activation_post_process_name, activation_post_process_ctr()
                )
        layer.layer_fw.cell = cell  # type: ignore[union-attr]
    return quantizable_lstm
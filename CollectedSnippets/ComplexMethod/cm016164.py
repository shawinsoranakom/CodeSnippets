def test_rnns(
    experim_creator,
    control_creator,
    check_grad=True,
    verbose=False,
    seqLength=100,
    numLayers=1,
    inputSize=512,
    hiddenSize=512,
    miniBatch=64,
    device="cuda",
    seed=17,
):
    creator_args = dict(
        seqLength=seqLength,
        numLayers=numLayers,
        inputSize=inputSize,
        hiddenSize=hiddenSize,
        miniBatch=miniBatch,
        device=device,
        seed=seed,
    )

    print("Setting up...")
    control = control_creator(**creator_args)
    experiment = experim_creator(**creator_args)

    # Precondition
    assertEqual(experiment.inputs, control.inputs)
    assertEqual(experiment.params, control.params)

    print("Checking outputs...")
    control_outputs = control.forward(*control.inputs)
    experim_outputs = experiment.forward(*experiment.inputs)
    assertEqual(experim_outputs, control_outputs)

    print("Checking grads...")
    if control.backward_setup is None:
        raise AssertionError("control.backward_setup must not be None")
    if experiment.backward_setup is None:
        raise AssertionError("experiment.backward_setup must not be None")
    if control.backward is None:
        raise AssertionError("control.backward must not be None")
    if experiment.backward is None:
        raise AssertionError("experiment.backward must not be None")
    control_backward_inputs = control.backward_setup(control_outputs, seed)
    experim_backward_inputs = experiment.backward_setup(experim_outputs, seed)

    control.backward(*control_backward_inputs)
    experiment.backward(*experim_backward_inputs)

    control_grads = [p.grad for p in control.params]
    experim_grads = [p.grad for p in experiment.params]
    assertEqual(experim_grads, control_grads)

    if verbose:
        print(experiment.forward.graph_for(*experiment.inputs))
    print()
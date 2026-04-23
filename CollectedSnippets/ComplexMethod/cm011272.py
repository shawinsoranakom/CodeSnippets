def _find_loss_output(mod: torch.nn.Module, g: fx.Graph, output_loss_value_spec):
    output_nodes = [n for n in g.nodes if n.op == "output"]
    if not len(output_nodes) == 1:
        raise AssertionError(f"Expected 1 output node, got {len(output_nodes)}")
    output_node = output_nodes[0]
    output_val = output_node.args[0]
    generated_spec: Any = None

    if isinstance(mod, TrivialLossWrapper):
        # TrivialLossWrapper is pre-defined by PiPPy.
        # It has loss as the only output so we can safely assume the first output arg is the loss.
        if not len(output_node.args) == 1:
            raise AssertionError(f"Expected 1 output arg, got {len(output_node.args)}")
        loss_node = output_val
        generated_spec = TrivialLossWrapper.loss_spec
    elif output_loss_value_spec is None:
        # Use default spec, i.e. search for "loss" in output values
        if isinstance(output_val, dict) and "loss" in output_val:
            loss_node = output_val["loss"]
            generated_spec = {k: k == "loss" for k in output_val}
        else:
            loss_node = None
            generated_spec = None
    else:
        loss_node = _find_loss_from_output_and_spec(output_val, output_loss_value_spec)
        generated_spec = output_loss_value_spec

    return loss_node, output_node, generated_spec
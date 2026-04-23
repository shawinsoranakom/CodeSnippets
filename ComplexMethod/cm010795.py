def can_offload(
    node: fx.Node,
    fwd_outputs: OrderedSet[fx.Node],
    model_outputs: OrderedSet[fx.Node],
    static_lifetime_input_nodes: OrderedSet[fx.Node],
) -> bool:
    """
    Determine if a node can be offloaded to CPU.

    Args:
        node: The node to check
        fwd_outputs: Forward module outputs, including model outputs and activations
        model_outputs: Model outputs

    NOTE: Additional context for the logic behind these offloading checks:

    * fwd_outputs: Only saved intermediate tensors should be offloaded.

    * model_outputs / static_lifetime_input_nodes: Tensors that may be accessed outside
      the compiled region (e.g., model outputs, static inputs) cannot be offloaded as
      they must remain accessible beyond the scope of the compiled graph.

    * views / getitems: Offloading such nodes can lead to segmentation faults.

    * contiguous: Offloading non-contiguous tensors causes CPU-side stride changes
      during both forward and backward passes when using the Inductor backend. While
      these stride changes cancel each other out, they introduce significant compute
      overhead. This is due to the contiguity check in ir.py (see link below).
      TODO: This restriction could potentially be bypassed in the future.
      Reference: https://github.com/pytorch/pytorch/blob/44ac69388a4a5eb463dbd2a13f00d1e3b924566c/torch/_inductor/ir.py#L3214

    Additional criteria to consider for offloading optimization:

    * Tensor size: Small tensors may not fully utilize available bandwidth, reducing the
      efficiency gains from offloading.

    * Position in forward/backward graph: Activations generated near the end of the forward
      pass are typically consumed near the beginning of the backward pass. Offloading such
      tensors may be counterproductive since they are quickly reloaded, not having sufficient
      time to overlap the transfer with computation.
    """

    log.debug(f"Checking node {node.name} for offloading...")  # noqa: G004

    op_types: OpTypes = get_default_op_list()

    if node not in fwd_outputs:
        log.debug("\tSkipped! Can only offload nodes in fwd_module_outputs.")
        return False
    if node in model_outputs:
        log.debug("\tSkipped! Cannot offload model outputs.")
        return False
    if node in static_lifetime_input_nodes:
        log.debug("\tSkipped! Cannot offload static input nodes.")
        return False
    if op_types.is_view(node):
        log.debug("\tSkipped! Cannot offload views.")
        return False
    if node.target == operator.getitem:
        log.debug("\tSkipped! Cannot offload getitems.")
        return False
    if hasattr(node, "meta") and "val" in node.meta:
        if (
            isinstance(val := node.meta["val"], torch.Tensor)
            and not val.is_contiguous()
        ):
            log.debug("\tSkipped! Cannot offload non-contiguous tensors.")
            return False

    log.debug("\tGood!")
    return True
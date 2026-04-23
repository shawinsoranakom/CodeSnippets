def mutate_to(changed, val, unsafe_alias=False):
    if isinstance(changed, TensorBox):
        changed_data = changed.data
    else:
        changed_data = changed
    if isinstance(val, TensorBox):
        val = val.data

    if not isinstance(val, ir.StorageBox):
        # introduce a copy to handle views
        node = Pointwise.create(
            device=changed.get_device(),
            dtype=changed.get_dtype(),
            inner_fn=val.make_loader(),
            ranges=changed.get_size(),
        )
        assert isinstance(node, (BaseView, MutableBox))
        val = node.data
        assert isinstance(val, ir.StorageBox)

    if isinstance(changed_data, ir.StorageBox) and not (
        changed_data.is_input_buffer()
        # In AOTI, module parameters and buffers are not lifted as graph inputs
        or changed_data.is_module_buffer()
        or isinstance(changed_data.data, ir.NopKernel)
    ):
        # Fast path, just swing the data pointer
        val.realize()
        changed_data.data = val.data
        return changed

    ir.MutationLayoutSHOULDREMOVE.realize_into(
        val, changed_data, unsafe_alias=unsafe_alias
    )
    return changed
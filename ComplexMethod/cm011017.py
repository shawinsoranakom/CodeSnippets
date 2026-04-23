def _device_mesh_reconstruct_fn(
    mesh: "OpaqueBase",
    get_tracked_proxy: Callable[["OpaqueBase"], "torch.fx.Proxy | None"],
    tracer: Any,
) -> "torch.fx.Proxy | None":
    """Reconstruct a DeviceMesh submesh from a tracked ancestor mesh.

    Called by PythonKeyTracer when make_fx encounters a DeviceMesh that isn't
    tracked (e.g. a submesh captured by a backward closure). Looks for any
    tracked mesh that shares the same root and contains the target dim names,
    then emits a call_function node that derives the submesh via _get_submesh.
    """
    if not isinstance(mesh, DeviceMesh):
        raise AssertionError("DeviceMesh expected")

    root_mesh = mesh._get_root_mesh()

    # Only submeshes can be reconstructed; root meshes must already be tracked.
    if mesh is root_mesh:
        return None

    dim_names = mesh._mesh_dim_names
    if dim_names is None:
        return None

    # Ensure the custom ops are registered
    from torch.distributed._ops import device_mesh as _dm_ops  # noqa: F401

    # Try the root mesh first (original path).
    ancestor_proxy = get_tracked_proxy(root_mesh)
    ancestor_dim_names = root_mesh._mesh_dim_names

    # If root isn't tracked, search for any tracked DeviceMesh that shares
    # the same root AND contains all our dim names. This handles the case
    # where e.g. a concatenated (fsdp, tp) mesh is a graph input (from
    # DTensor.__tensor_flatten__) but neither root nor the individual
    # submeshes are tracked directly.
    if ancestor_proxy is None:
        from torch._library.fake_class_registry import FakeScriptObject

        for tracked_obj, proxy in tracer.opaque_tracker.items():
            real_obj = (
                tracked_obj.real_obj
                if isinstance(tracked_obj, FakeScriptObject)
                else tracked_obj
            )
            if not isinstance(real_obj, DeviceMesh) or real_obj is mesh:
                continue
            if real_obj._get_root_mesh() is not root_mesh:
                continue
            tracked_dim_names = real_obj._mesh_dim_names
            if tracked_dim_names is None:
                continue
            if all(n in tracked_dim_names for n in dim_names):
                ancestor_proxy = proxy
                ancestor_dim_names = tracked_dim_names
                break

    if ancestor_proxy is None or ancestor_dim_names is None:
        return None

    # Convert our dim names to indices into the ancestor mesh's dim names
    mesh_dims = [ancestor_dim_names.index(n) for n in dim_names]

    # Dispatch through the custom op with proxy mode active so that
    # meta["val"] is set and the result is tracked in opaque_tracker.
    return torch.ops.device_mesh._get_submesh(ancestor_proxy, mesh_dims)
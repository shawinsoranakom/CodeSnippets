def _expand_group(group: RANK_TYPES, tag: str = "") -> tuple[str, list[int], int]:
    """
    _expand_group desugars the different RANK_TYPES types into a canonical format that is traceable.

    By having this be part of the explicit eager codepath, we avoid having to specialize behavior inside
    torchdynamo and can still interoperate with processgroup objects or other untraceable forms.
    """
    # had to define this hack _inside_ expand_group to avoid
    # graph_break [('torch.* op returned non-Tensor int
    # caused by 'cast_*` functions being treated as 'torch.*' ops (iiuc)
    if TYPE_CHECKING:

        def cast_listlistint(x):
            return cast(list[list[int]], x)

        def cast_listint(x):
            return cast(list[int], x)

    else:
        # fake cast op for use at runtime since dynamo doesn't support real cast
        # also, dynamo didn't like encountering 'typing' objects ()
        # NotImplementedError: argument of type: <class 'typing._GenericAlias'>
        def cast_listlistint(x):
            return x

        def cast_listint(x):
            return x

    rankset: list[int]
    if isinstance(group, list):
        if isinstance(group[0], list):
            nested_list = cast_listlistint(group)
            rankset = []
            group_size = -1
            for rs in nested_list:
                rankset.extend(rs)
                if group_size != -1 and group_size != len(rs):
                    raise ValueError(
                        f"group sizes must be identical found {group_size} and {len(rs)}"
                    )
                group_size = len(rs)
        else:
            rankset = cast_listint(group)
            group_size = len(rankset)
    elif isinstance(group, dist.ProcessGroup):
        rankset = dist.get_process_group_ranks(group)
        group_size = len(rankset)
        tag = tag or c10d._get_group_tag(group)
    elif isinstance(group, DeviceMesh):
        if group.ndim != 1:
            raise AssertionError(
                "Only 1D mesh is supported, pass in (DeviceMesh, int) together if mesh > 1D"
            )
        pg = group.get_group()
        rankset = dist.get_process_group_ranks(pg)
        group_size = len(rankset)
        tag = tag or c10d._get_group_tag(pg)
    elif isinstance(group, tuple):
        if (
            len(group) == 2
            and isinstance(group[0], DeviceMesh)
            and isinstance(group[1], int)
        ):
            dmesh = group[0]
            dim = group[1]
            pg = dmesh.get_group(dim)
            rankset = dist.get_process_group_ranks(pg)
            group_size = len(rankset)
            tag = tag or c10d._get_group_tag(pg)
        else:
            raise ValueError("Invalid tuple for group must be (DeviceMesh, int)")
    else:
        raise ValueError(
            "Invalid type for group, must be one of List, Processgroup, DeviceMesh or (DeviceMesh, int)."
        )

    return (tag, rankset, group_size)
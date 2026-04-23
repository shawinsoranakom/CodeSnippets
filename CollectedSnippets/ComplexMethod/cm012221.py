def get_view_shape_list(cat_arg: torch.fx.Node, stack_dim: int) -> list[int]:
    # cat_arg must be the split input
    view_shape_list = []
    for user in cat_arg.users:
        if user.target is torch.split:
            for getitem in user.users:
                if getitem.target is operator.getitem:
                    reshape_user = [
                        user for user in getitem.users if user.target is torch.reshape
                    ]
                    if len(reshape_user) > 0:
                        view_shape_list = list(
                            reshape_user[0]
                            .meta["example_value"]
                            .unsqueeze(stack_dim)
                            .shape
                        )
                        view_shape_list[stack_dim] = -1
                        return view_shape_list
    return view_shape_list
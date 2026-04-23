def get_output_tokens(node: torch.fx.Node) -> set[torch.fx.Node]:
        output_tokens = set()
        for user in list(node.users.keys()):
            # Check if this is a getitem accessing index 0 (the token)
            if (
                user.op == "call_function"
                and user.target is operator.getitem
                and len(user.args) > 1
                and user.args[1] == 0
            ):
                # Check if this getitem is used in an output
                for user_user in list(user.users.keys()):
                    if user_user.op == "output":
                        output_tokens.add(user)
        return output_tokens
def convert_to_fake(x: Any) -> Any:
            if is_namedtuple(x):
                return type(x)(*(convert_to_fake(elem) for elem in x))
            elif isinstance(x, dict):
                return {k: convert_to_fake(v) for k, v in x.items()}  # type: ignore[misc]
            elif isinstance(x, (list, tuple, set)):
                return type(x)(convert_to_fake(elem) for elem in x)
            elif isinstance(x, torch.fx.Proxy):
                return get_fake_value(x.node, tx)
            else:
                return x
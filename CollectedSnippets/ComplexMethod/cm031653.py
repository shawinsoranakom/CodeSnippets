def _format(node: Any, level: int = 0) -> tuple[str, bool]:
        if indent is not None:
            level += 1
            prefix = "\n" + indent * level
            sep = ",\n" + indent * level
        else:
            prefix = ""
            sep = ", "
        if any(cls.__name__ == "AST" for cls in node.__class__.__mro__):
            cls = type(node)
            args = []
            allsimple = True
            keywords = annotate_fields
            for name in node._fields:
                try:
                    value = getattr(node, name)
                except AttributeError:
                    keywords = True
                    continue
                if value is None and getattr(cls, name, ...) is None:
                    keywords = True
                    continue
                value, simple = _format(value, level)
                allsimple = allsimple and simple
                if keywords:
                    args.append(f"{name}={value}")
                else:
                    args.append(value)
            if include_attributes and node._attributes:
                for name in node._attributes:
                    try:
                        value = getattr(node, name)
                    except AttributeError:
                        continue
                    if value is None and getattr(cls, name, ...) is None:
                        continue
                    value, simple = _format(value, level)
                    allsimple = allsimple and simple
                    args.append(f"{name}={value}")
            if allsimple and len(args) <= 3:
                return "{}({})".format(node.__class__.__name__, ", ".join(args)), not args
            return f"{node.__class__.__name__}({prefix}{sep.join(args)})", False
        elif isinstance(node, list):
            if not node:
                return "[]", True
            return f"[{prefix}{sep.join(_format(x, level)[0] for x in node)}]", False
        return repr(node), True
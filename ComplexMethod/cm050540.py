def _change_operator(domain):
            new_domain = []
            for dom in domain:
                if len(dom) == 3:
                    _, op, value = dom
                    if op in ("any", "not any"):
                        new_op = "in" if op == "any" else "not in"
                        ids = [val[2] for val in value if isinstance(val, (tuple, list)) and isinstance(val[2], int)]
                        new_domain.append(("id", new_op, ids))
                        continue
                    op = "ilike" if op == "child_of" else op
                    if isinstance(value, list) and all(isinstance(val, int) for val in value):
                        new_domain.append(("id", op, value))
                    elif isinstance(value, str) or (isinstance(value, list) and not all(isinstance(val, str) for val in value)):
                        new_domain.append(("name", op, value))
                    if isinstance(value, int):
                        if op == "=":
                            op = "in"
                        if op == "!=":
                            op = "not in"
                        new_domain.append(("id", op, [value]))
                else:
                    new_domain.append(dom)
            return Domain(new_domain)
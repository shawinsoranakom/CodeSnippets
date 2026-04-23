def optimizer(cls, domains: list[Domain], model):
            # trick: result remains None until an optimization is applied, after
            # which it becomes the optimization of domains[:index]
            result = None
            # when not None, domains[block:index] are all conditions with the same field_expr
            block = None

            domains_iterator = enumerate(domains)
            stop_item = (len(domains), None)
            while True:
                # enumerating domains and adding the stop_item as the sentinel
                # so that the last loop merges the domains and stops the iteration
                index, domain = next(domains_iterator, stop_item)
                matching = isinstance(domain, DomainCondition) and domain.operator in operators

                if block is not None and not (matching and domain.field_expr == domains[block].field_expr):
                    # optimize domains[block:index] if necessary and "flush" them in result
                    if block < index - 1 and (
                        field_types is None or domains[block]._field(model).type in field_types
                    ):
                        if result is None:
                            result = domains[:block]
                        result.extend(optimization(cls, domains[block:index], model))
                    elif result is not None:
                        result.extend(domains[block:index])
                    block = None

                # block is None or (matching and domain.field_expr == domains[block].field_expr)
                if domain is None:
                    break
                if matching:
                    if block is None:
                        block = index
                elif result is not None:
                    result.append(domain)

            # block is None
            return domains if result is None else result
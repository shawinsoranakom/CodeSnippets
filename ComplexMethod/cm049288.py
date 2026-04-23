def _get_read_group_order(self, dict_order: dict[str, str], groupby: list[str], aggregates: Sequence[str]) -> str:
        if not dict_order:
            return ", ".join(groupby)

        groupby = list(groupby)
        order_spec = []
        for fname, direction in dict_order.items():
            if fname == '__count':
                order_spec.append(f"{fname} {direction}")
                continue
            for group in list(groupby):
                if fname == group or group.startswith(f"{fname}:"):
                    groupby.remove(group)
                    order_spec.append(f"{group} {direction}")
                    break
            else:
                for agg_spec in aggregates:
                    if agg_spec.startswith(f"{fname}:"):
                        order_spec.append(f"{agg_spec} {direction}")
                        break
                else:
                    field = self._fields.get(fname)
                    if field and field.aggregator:
                        order_spec.append(f"{fname}:{field.aggregator} {direction}")

        return ", ".join(order_spec + groupby)
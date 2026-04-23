def _handle_order_with_respect_to(self, objs):
        if objs and (order_wrt := self.model._meta.order_with_respect_to):
            get_filter_kwargs_for_object = order_wrt.get_filter_kwargs_for_object
            attnames = list(get_filter_kwargs_for_object(objs[0]))
            group_keys = set()
            obj_groups = []
            for obj in objs:
                group_key = tuple(get_filter_kwargs_for_object(obj).values())
                group_keys.add(group_key)
                obj_groups.append((obj, group_key))
            filters = [
                Q.create(list(zip(attnames, group_key))) for group_key in group_keys
            ]
            next_orders = (
                self.model._base_manager.using(self.db)
                .filter(reduce(operator.or_, filters))
                .values_list(*attnames)
                .annotate(_order__max=Max("_order") + 1)
            )
            # Create mapping of group values to max order.
            group_next_orders = dict.fromkeys(group_keys, 0)
            group_next_orders.update(
                (tuple(group_key), next_order) for *group_key, next_order in next_orders
            )
            # Assign _order values to new objects.
            for obj, group_key in obj_groups:
                if getattr(obj, "_order", None) is None:
                    group_next_order = group_next_orders[group_key]
                    obj._order = group_next_order
                    group_next_orders[group_key] += 1
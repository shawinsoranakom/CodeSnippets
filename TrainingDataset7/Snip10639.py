def _get_next_or_previous_in_order(self, is_next):
        cachename = "__%s_order_cache" % is_next
        if not hasattr(self, cachename):
            op = "gt" if is_next else "lt"
            order = "_order" if is_next else "-_order"
            order_field = self._meta.order_with_respect_to
            filter_args = order_field.get_filter_kwargs_for_object(self)
            obj = (
                self.__class__._default_manager.filter(**filter_args)
                .filter(
                    **{
                        "_order__%s"
                        % op: self.__class__._default_manager.values("_order").filter(
                            **{self._meta.pk.name: self.pk}
                        )
                    }
                )
                .order_by(order)[:1]
                .get()
            )
            setattr(self, cachename, obj)
        return getattr(self, cachename)
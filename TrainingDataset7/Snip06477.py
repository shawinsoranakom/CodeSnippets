def make_generic_foreign_order_accessors(related_model, model):
                if self._is_matching_generic_foreign_key(
                    model._meta.order_with_respect_to
                ):
                    make_foreign_order_accessors(model, related_model)
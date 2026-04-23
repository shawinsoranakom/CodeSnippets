def setup_nonrelated(self, model):
        super().setup_nonrelated(model)
        # 3 cases:
        # 1) The ondelete attribute is not defined, we assign it a sensible default
        # 2) The ondelete attribute is defined and its definition makes sense
        # 3) The ondelete attribute is explicitly defined as 'set null' for a required m2o,
        #    this is considered a programming error.
        if not self.ondelete:
            comodel = model.env[self.comodel_name]
            if model.is_transient() and not comodel.is_transient():
                # Many2one relations from TransientModel Model are annoying because
                # they can block deletion due to foreign keys. So unless stated
                # otherwise, we default them to ondelete='cascade'.
                self.ondelete = 'cascade' if self.required else 'set null'
            else:
                self.ondelete = 'restrict' if self.required else 'set null'
        if self.ondelete == 'set null' and self.required:
            raise ValueError(
                "The m2o field %s of model %s is required but declares its ondelete policy "
                "as being 'set null'. Only 'restrict' and 'cascade' make sense."
                % (self.name, model._name)
            )
        if self.ondelete == 'restrict' and self.comodel_name in IR_MODELS:
            raise ValueError(
                f"Field {self.name} of model {model._name} is defined as ondelete='restrict' "
                f"while having {self.comodel_name} as comodel, the 'restrict' mode is not "
                f"supported for this type of field as comodel."
            )
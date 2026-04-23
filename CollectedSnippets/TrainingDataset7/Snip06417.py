def __init__(
        self, ct_field="content_type", fk_field="object_id", for_concrete_model=True
    ):
        super().__init__(editable=False)
        self.ct_field = ct_field
        self.fk_field = fk_field
        self.for_concrete_model = for_concrete_model
        self.is_relation = True
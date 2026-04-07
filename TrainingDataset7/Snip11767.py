def set_wrapper_classes(self, connection=None):
        # Some databases (e.g. MySQL) treats COLLATE as an indexed expression.
        if connection and connection.features.collate_as_index_expression:
            self.wrapper_classes = tuple(
                [
                    wrapper_cls
                    for wrapper_cls in self.wrapper_classes
                    if wrapper_cls is not Collate
                ]
            )
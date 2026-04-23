def formatted_description(self):
        """Output a description prefixed by a category symbol."""
        description = self.describe()
        if self.category is None:
            return f"{OperationCategory.MIXED.value} {description}"
        return f"{self.category.value} {description}"
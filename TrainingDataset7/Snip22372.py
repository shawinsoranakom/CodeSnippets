def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, ArticleTranslationDescriptor(self))
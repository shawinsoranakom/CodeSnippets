def __get__(self, instance, cls=None):
        if instance is None:
            return self

        # This is slightly complicated, so worth an explanation.
        # instance.file needs to ultimately return some instance of `File`,
        # probably a subclass. Additionally, this returned object needs to have
        # the FieldFile API so that users can easily do things like
        # instance.file.path and have that delegated to the file storage
        # engine. Easy enough if we're strict about assignment in __set__, but
        # if you peek below you can see that we're not. So depending on the
        # current value of the field we have to dynamically construct some sort
        # of "thing" to return.

        # The instance dict contains whatever was originally assigned
        # in __set__.
        file = super().__get__(instance, cls)

        # If this value is a string (instance.file = "path/to/file") or None
        # then we simply wrap it with the appropriate attribute class according
        # to the file field. [This is FieldFile for FileFields and
        # ImageFieldFile for ImageFields; it's also conceivable that user
        # subclasses might also want to subclass the attribute class]. This
        # object understands how to convert a path to a file, and also how to
        # handle None.
        if isinstance(file, str) or file is None:
            attr = self.field.attr_class(instance, self.field, file)
            instance.__dict__[self.field.attname] = attr

        # If this value is a DatabaseDefault, initialize the attribute class
        # for this field with its db_default value.
        elif isinstance(file, DatabaseDefault):
            attr = self.field.attr_class(instance, self.field, self.field.db_default)
            instance.__dict__[self.field.attname] = attr

        # Other types of files may be assigned as well, but they need to have
        # the FieldFile interface added to them. Thus, we wrap any other type
        # of File inside a FieldFile (well, the field's attr_class, which is
        # usually FieldFile).
        elif isinstance(file, File) and not isinstance(file, FieldFile):
            file_copy = self.field.attr_class(instance, self.field, file.name)
            file_copy.file = file
            file_copy._committed = False
            instance.__dict__[self.field.attname] = file_copy

        # Finally, because of the (some would say boneheaded) way pickle works,
        # the underlying FieldFile might not actually itself have an associated
        # file. So we need to reset the details of the FieldFile in those
        # cases.
        elif isinstance(file, FieldFile) and not hasattr(file, "field"):
            file.instance = instance
            file.field = self.field
            file.storage = self.field.storage

        # Make sure that the instance is correct.
        elif isinstance(file, FieldFile) and instance is not file.instance:
            file.instance = instance

        # That was fun, wasn't it?
        return instance.__dict__[self.field.attname]
def schema_editor(self, *args, **kwargs):
        """
        Return a new instance of this backend's SchemaEditor.
        """
        if self.SchemaEditorClass is None:
            raise NotImplementedError(
                "The SchemaEditorClass attribute of this database wrapper is still None"
            )
        return self.SchemaEditorClass(self, *args, **kwargs)
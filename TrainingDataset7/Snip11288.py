def pre_save(self, model_instance, add):
        file = super().pre_save(model_instance, add)
        if file.name is None and file._file is not None:
            exc = FieldError(
                f"File for {self.name} must have "
                "the name attribute specified to be saved."
            )
            if isinstance(file._file, ContentFile):
                exc.add_note("Pass a 'name' argument to ContentFile.")
            raise exc

        if file and not file._committed:
            # Commit the file to storage prior to saving the model
            file.save(file.name, file.file, save=False)
        return file
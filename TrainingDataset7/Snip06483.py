def save_new(self, form, commit=True):
        setattr(
            form.instance,
            self.ct_field.attname,
            ContentType.objects.get_for_model(self.instance).pk,
        )
        setattr(form.instance, self.ct_fk_field.attname, self.instance.pk)
        return form.save(commit=commit)
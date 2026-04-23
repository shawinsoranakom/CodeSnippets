def callback(db_field, **kwargs):
            if isinstance(db_field, models.CharField):
                return forms.CharField(widget=forms.Textarea)
            return db_field.formfield(**kwargs)
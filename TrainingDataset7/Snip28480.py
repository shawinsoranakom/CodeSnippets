def formfield_for_dbfield(db_field, **kwargs):
            if db_field.name == "categories":
                kwargs["initial"] = lambda: Category.objects.order_by("name")[:2]
            return db_field.formfield(**kwargs)
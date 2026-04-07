def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        first_name, last_name = form.instance.name.split()
        for child in form.instance.child_set.all():
            if len(child.name.split()) < 2:
                child.name = child.name + " " + last_name
                child.save()
def view_on_site(self, obj):
        return "/worker_inline/%s/%s/" % (obj.surname, obj.name)
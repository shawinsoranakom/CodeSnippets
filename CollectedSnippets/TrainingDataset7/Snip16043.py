def view_on_site(self, obj):
        return "/worker/%s/%s/" % (obj.surname, obj.name)
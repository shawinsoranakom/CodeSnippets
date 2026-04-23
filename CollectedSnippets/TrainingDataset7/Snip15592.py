def get_ordering(self, request):
        if request.user.is_superuser:
            return ["rank"]
        else:
            return ["name"]
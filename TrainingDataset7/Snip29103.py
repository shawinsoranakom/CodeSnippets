def get_list_filter(self, request):
                if getattr(request, "user", None):
                    return self.list_filter + ["main_band__name"]
                return self.list_filter
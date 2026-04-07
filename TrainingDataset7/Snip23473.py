def get_inlines(self, request, obj):
                if hasattr(request, "name"):
                    if request.name == "alternate":
                        return self.inlines[:1]
                    elif request.name == "media":
                        return self.inlines[1:2]
                return []
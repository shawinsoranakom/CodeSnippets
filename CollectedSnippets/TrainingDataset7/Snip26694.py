def get_xframe_options_value(self, request, response):
                if getattr(request, "sameorigin", False):
                    return "SAMEORIGIN"
                if getattr(response, "sameorigin", False):
                    return "SAMEORIGIN"
                return "DENY"
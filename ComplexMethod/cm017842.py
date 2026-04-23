def get_post_parameters(self, request):
        """
        Replace the values of POST parameters marked as sensitive with
        stars (*********).
        """
        if request is None:
            return {}
        else:
            sensitive_post_parameters = getattr(
                request, "sensitive_post_parameters", []
            )
            if self.is_active(request) and sensitive_post_parameters:
                cleansed = request.POST.copy()
                if sensitive_post_parameters == "__ALL__":
                    # Cleanse all parameters.
                    for k in cleansed:
                        cleansed[k] = self.cleansed_substitute
                    return cleansed
                else:
                    # Cleanse only the specified parameters.
                    for param in sensitive_post_parameters:
                        if param in cleansed:
                            cleansed[param] = self.cleansed_substitute
                    return cleansed
            else:
                return request.POST
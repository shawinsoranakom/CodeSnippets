def swapped(self):
        """
        Has this model been swapped out for another? If so, return the model
        name of the replacement; otherwise, return None.

        For historical reasons, model name lookups using get_model() are
        case insensitive, so we make sure we are case insensitive here.
        """
        if self.swappable:
            swapped_for = getattr(settings, self.swappable, None)
            if swapped_for:
                try:
                    swapped_label, swapped_object = swapped_for.split(".")
                except ValueError:
                    # setting not in the format app_label.model_name
                    # raising ImproperlyConfigured here causes problems with
                    # test cleanup code - instead it is raised in
                    # get_user_model or as part of validation.
                    return swapped_for

                if (
                    "%s.%s" % (swapped_label, swapped_object.lower())
                    != self.label_lower
                ):
                    return swapped_for
        return None
def id_for_label(self, id_):
        """
        Return the HTML ID attribute of this Widget for use by a <label>, given
        the ID of the field. Return an empty string if no ID is available.

        This hook is necessary because some widgets have multiple HTML
        elements and, thus, multiple IDs. In that case, this method should
        return an ID value that corresponds to the first ID in the widget's
        tags.
        """
        return id_
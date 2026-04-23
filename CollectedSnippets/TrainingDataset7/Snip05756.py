def get_list_select_related(self, request):
        """
        Return a list of fields to add to the select_related() part of the
        changelist items query.
        """
        return self.list_select_related
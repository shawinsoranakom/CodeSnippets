def get_changelist(self, request, **kwargs):
        """
        Return the ChangeList class for use on the changelist page.
        """
        from django.contrib.admin.views.main import ChangeList

        return ChangeList
def get_week(self):
        """Return the week for which this view should display data."""
        week = self.week
        if week is None:
            try:
                week = self.kwargs["week"]
            except KeyError:
                try:
                    week = self.request.GET["week"]
                except KeyError:
                    raise Http404(_("No week specified"))
        return week
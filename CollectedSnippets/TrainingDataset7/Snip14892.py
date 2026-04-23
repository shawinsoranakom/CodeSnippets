def get_month(self):
        """Return the month for which this view should display data."""
        month = self.month
        if month is None:
            try:
                month = self.kwargs["month"]
            except KeyError:
                try:
                    month = self.request.GET["month"]
                except KeyError:
                    raise Http404(_("No month specified"))
        return month
def get_day(self):
        """Return the day for which this view should display data."""
        day = self.day
        if day is None:
            try:
                day = self.kwargs["day"]
            except KeyError:
                try:
                    day = self.request.GET["day"]
                except KeyError:
                    raise Http404(_("No day specified"))
        return day
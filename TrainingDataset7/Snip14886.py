def get_year(self):
        """Return the year for which this view should display data."""
        year = self.year
        if year is None:
            try:
                year = self.kwargs["year"]
            except KeyError:
                try:
                    year = self.request.GET["year"]
                except KeyError:
                    raise Http404(_("No year specified"))
        return year
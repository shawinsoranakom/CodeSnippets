class SpendingByCategory(MRJob):

    def __init__(self, categorizer):
        self.categorizer = categorizer
        ...

    def current_year_month(self):
        """Return the current year and month."""
        ...

    def extract_year_month(self, timestamp):
        """Return the year and month portions of the timestamp."""
        ...

    def handle_budget_notifications(self, key, total):
        """Call notification API if nearing or exceeded budget."""
        ...

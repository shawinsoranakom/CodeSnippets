def disable(self):
        self.catch_warnings.__exit__(*sys.exc_info())
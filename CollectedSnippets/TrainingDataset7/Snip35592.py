def tearDown(self):
        self.atomic.__exit__(*sys.exc_info())
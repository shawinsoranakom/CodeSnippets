def clean(self):
        if self.pub_date is None:
            self.pub_date = datetime.now()
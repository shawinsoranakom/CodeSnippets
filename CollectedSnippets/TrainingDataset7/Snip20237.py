def was_published_today(self):
        return self.pub_date == datetime.date.today()
def decade_published_in(self):
        return self.pub_date.strftime("%Y")[:3] + "0's"
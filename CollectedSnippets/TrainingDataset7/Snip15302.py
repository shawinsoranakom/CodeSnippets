def rename_company(self, new_name):
        self.company.name = new_name
        self.company.save()
        return new_name
def delete(self):
        self.data.append("Before deletion")
        # Call the "real" delete() method
        super().delete()
        self.data.append("After deletion")
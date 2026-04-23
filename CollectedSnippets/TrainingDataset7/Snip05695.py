def get_edited_object(self):
        """Return the edited object represented by this log entry."""
        return self.content_type.get_object_for_this_type(pk=self.object_id)
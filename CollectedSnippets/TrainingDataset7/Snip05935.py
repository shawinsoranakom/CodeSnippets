def serialize_result(self, obj, to_field_name):
        """
        Convert the provided model object to a dictionary that is added to the
        results list.
        """
        return {"id": str(getattr(obj, to_field_name)), "text": str(obj)}
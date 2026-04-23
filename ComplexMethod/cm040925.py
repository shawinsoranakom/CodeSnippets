def fake_secret_to_dict(fn, self):
    res_dict = fn(self)
    if self.last_accessed_date:
        res_dict["LastAccessedDate"] = self.last_accessed_date
    if not self.description and "Description" in res_dict:
        del res_dict["Description"]
    if not self.rotation_enabled and "RotationEnabled" in res_dict:
        del res_dict["RotationEnabled"]
    if self.auto_rotate_after_days is None and "RotationRules" in res_dict:
        del res_dict["RotationRules"]
    if self.tags is None and "Tags" in res_dict:
        del res_dict["Tags"]
    for null_field in [key for key, value in res_dict.items() if value is None]:
        del res_dict[null_field]
    return res_dict
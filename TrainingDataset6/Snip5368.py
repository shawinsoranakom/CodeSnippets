def get_pet_type(v):
        assert isinstance(v, dict)
        return v.get("pet_type", "")
def __init__(self, profile_name: str) -> None:
        self.profile_name = profile_name

        profile = _serialization.get_serialization_profile(profile_name)

        supported_tags = {obj: None for obj in profile.serialize_map if issubclass(obj, AnsibleDatatagBase)}

        if supported_tags:
            self.supported_tag_values = tuple(tag_value for tag_type, tag_value in tag_values.items() if tag_type in supported_tags)

            if not self.supported_tag_values:
                raise Exception(f'Profile {profile} supports tags {supported_tags}, but no supported tag value is available.')
        else:
            self.supported_tag_values = tuple()

        self.unsupported_tag_value = next((tag_value for tag_type, tag_value in tag_values.items() if tag_type not in supported_tags), None)

        if not self.unsupported_tag_value and profile.profile_name != _cache_persistence._Profile.profile_name:
            raise Exception(f'Profile {profile} supports tags {supported_tags}, but no unsupported tag value is available.')
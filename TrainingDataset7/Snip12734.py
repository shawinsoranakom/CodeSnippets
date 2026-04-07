def __reduce_ex__(self, *args, **kwargs):
        # The `list` reduce function returns an iterator as the fourth element
        # that is normally used for repopulating. Since we only inherit from
        # `list` for `isinstance` backward compatibility (Refs #17413) we
        # nullify this iterator as it would otherwise result in duplicate
        # entries. (Refs #23594)
        info = super(UserList, self).__reduce_ex__(*args, **kwargs)
        return info[:3] + (None, None)
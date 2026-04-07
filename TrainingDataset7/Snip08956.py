def deserialize(format, stream_or_string, **options):
    """
    Deserialize a stream or a string. Return an iterator that yields ``(obj,
    m2m_relation_dict)``, where ``obj`` is an instantiated -- but *unsaved* --
    object, and ``m2m_relation_dict`` is a dictionary of ``{m2m_field_name :
    list_of_related_objects}``.
    """
    d = get_deserializer(format)
    return d(stream_or_string, **options)
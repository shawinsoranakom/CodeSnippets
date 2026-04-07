def parse_rst(text, default_reference_context, thing_being_parsed=None):
    """
    Convert the string from reST to an XHTML fragment.
    """
    overrides = {
        "doctitle_xform": True,
        "initial_header_level": 3,
        "default_reference_context": default_reference_context,
        "link_base": reverse("django-admindocs-docroot").rstrip("/"),
        "raw_enabled": False,
        "file_insertion_enabled": False,
    }
    thing_being_parsed = thing_being_parsed and "<%s>" % thing_being_parsed
    # Wrap ``text`` in some reST that sets the default role to
    # ``cmsreference``, then restores it.
    source = """
.. default-role:: cmsreference

%s

.. default-role::
"""
    # In docutils < 0.22, the `writer` param must be an instance. Passing a
    # string writer name like "html" is only supported in 0.22+.
    writer_instance = docutils.writers.get_writer_class("html")()
    parts = docutils.core.publish_parts(
        source % text,
        source_path=thing_being_parsed,
        destination_path=None,
        writer=writer_instance,
        settings_overrides=overrides,
    )
    return mark_safe(parts["fragment"])
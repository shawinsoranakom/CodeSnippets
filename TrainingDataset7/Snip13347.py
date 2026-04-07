def regroup(parser, token):
    """
    Regroup a list of alike objects by a common attribute.

    This complex tag is best illustrated by use of an example: say that
    ``musicians`` is a list of ``Musician`` objects that have ``name`` and
    ``instrument`` attributes, and you'd like to display a list that
    looks like:

        * Guitar:
            * Django Reinhardt
            * Emily Remler
        * Piano:
            * Lovie Austin
            * Bud Powell
        * Trumpet:
            * Duke Ellington

    The following snippet of template code would accomplish this dubious task::

        {% regroup musicians by instrument as grouped %}
        <ul>
        {% for group in grouped %}
            <li>{{ group.grouper }}
            <ul>
                {% for musician in group.list %}
                <li>{{ musician.name }}</li>
                {% endfor %}
            </ul>
        {% endfor %}
        </ul>

    As you can see, ``{% regroup %}`` populates a variable with a list of
    objects with ``grouper`` and ``list`` attributes. ``grouper`` contains the
    item that was grouped by; ``list`` contains the list of objects that share
    that ``grouper``. In this case, ``grouper`` would be ``Guitar``, ``Piano``
    and ``Trumpet``, and ``list`` is the list of musicians who play this
    instrument.

    Note that ``{% regroup %}`` does not work when the list to be grouped is
    not sorted by the key you are grouping by! This means that if your list of
    musicians was not sorted by instrument, you'd need to make sure it is
    sorted before using it, i.e.::

        {% regroup musicians|dictsort:"instrument" by instrument as grouped %}
    """
    bits = token.split_contents()
    if len(bits) != 6:
        raise TemplateSyntaxError("'regroup' tag takes five arguments")
    target = parser.compile_filter(bits[1])
    if bits[2] != "by":
        raise TemplateSyntaxError("second argument to 'regroup' tag must be 'by'")
    if bits[4] != "as":
        raise TemplateSyntaxError("next-to-last argument to 'regroup' tag must be 'as'")
    var_name = bits[5]
    # RegroupNode will take each item in 'target', put it in the context under
    # 'var_name', evaluate 'var_name'.'expression' in the current context, and
    # group by the resulting value. After all items are processed, it will
    # save the final result in the context under 'var_name', thus clearing the
    # temporary values. This hack is necessary because the template engine
    # doesn't provide a context-aware equivalent of Python's getattr.
    expression = parser.compile_filter(
        var_name + VARIABLE_ATTRIBUTE_SEPARATOR + bits[3]
    )
    return RegroupNode(target, expression, var_name)
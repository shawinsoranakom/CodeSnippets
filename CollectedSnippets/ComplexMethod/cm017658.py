def cycle(parser, token):
    """
    Cycle among the given strings each time this tag is encountered.

    Within a loop, cycles among the given strings each time through
    the loop::

        {% for o in some_list %}
            <tr class="{% cycle 'row1' 'row2' %}">
                ...
            </tr>
        {% endfor %}

    Outside of a loop, give the values a unique name the first time you call
    it, then use that name each successive time through::

            <tr class="{% cycle 'row1' 'row2' 'row3' as rowcolors %}">...</tr>
            <tr class="{% cycle rowcolors %}">...</tr>
            <tr class="{% cycle rowcolors %}">...</tr>

    You can use any number of values, separated by spaces. Commas can also
    be used to separate values; if a comma is used, the cycle values are
    interpreted as literal strings.

    The optional flag "silent" can be used to prevent the cycle declaration
    from returning any value::

        {% for o in some_list %}
            {% cycle 'row1' 'row2' as rowcolors silent %}
            <tr class="{{ rowcolors }}">{% include "subtemplate.html " %}</tr>
        {% endfor %}
    """
    # Note: This returns the exact same node on each {% cycle name %} call;
    # that is, the node object returned from {% cycle a b c as name %} and the
    # one returned from {% cycle name %} are the exact same object. This
    # shouldn't cause problems (heh), but if it does, now you know.
    #
    # Ugly hack warning: This stuffs the named template dict into parser so
    # that names are only unique within each template (as opposed to using
    # a global variable, which would make cycle names have to be unique across
    # *all* templates.
    #
    # It keeps the last node in the parser to be able to reset it with
    # {% resetcycle %}.

    args = token.split_contents()

    if len(args) < 2:
        raise TemplateSyntaxError("'cycle' tag requires at least two arguments")

    if len(args) == 2:
        # {% cycle foo %} case.
        name = args[1]
        if not hasattr(parser, "_named_cycle_nodes"):
            raise TemplateSyntaxError(
                "No named cycles in template. '%s' is not defined" % name
            )
        if name not in parser._named_cycle_nodes:
            raise TemplateSyntaxError("Named cycle '%s' does not exist" % name)
        return parser._named_cycle_nodes[name]

    as_form = False

    if len(args) > 4:
        # {% cycle ... as foo [silent] %} case.
        if args[-3] == "as":
            if args[-1] != "silent":
                raise TemplateSyntaxError(
                    "Only 'silent' flag is allowed after cycle's name, not '%s'."
                    % args[-1]
                )
            as_form = True
            silent = True
            args = args[:-1]
        elif args[-2] == "as":
            as_form = True
            silent = False

    if as_form:
        name = args[-1]
        values = [parser.compile_filter(arg) for arg in args[1:-2]]
        node = CycleNode(values, name, silent=silent)
        if not hasattr(parser, "_named_cycle_nodes"):
            parser._named_cycle_nodes = {}
        parser._named_cycle_nodes[name] = node
    else:
        values = [parser.compile_filter(arg) for arg in args[1:]]
        node = CycleNode(values)
    parser._last_cycle_node = node
    return node
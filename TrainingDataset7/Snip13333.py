def debug(parser, token):
    """
    Output a whole load of debugging information, including the current
    context and imported modules.

    Sample usage::

        <pre>
            {% debug %}
        </pre>
    """
    return DebugNode()
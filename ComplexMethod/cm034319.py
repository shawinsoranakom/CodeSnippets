def _new_context(
    *,
    environment: Environment,
    template_name: str | None,
    blocks: dict[str, t.Callable[[Context], c.Iterator[str]]],
    shared: bool = False,
    jinja_locals: c.Mapping[str, t.Any] | None = None,
    jinja_vars: c.Mapping[str, t.Any] | None = None,
    jinja_globals: c.MutableMapping[str, t.Any] | None = None,
) -> Context:
    """Override Jinja's context vars setup to use ChainMaps and containers that support lazy templating."""
    layers = []

    if jinja_locals:
        # Omit values set to Jinja's internal `missing` sentinel; they are locals that have not yet been
        # initialized in the current context, and should not be exposed to child contexts. e.g.: {% import 'a' as b with context %}.
        # The `b` local will be `missing` in the `a` context and should not be propagated as a local to the child context we're creating.
        layers.append(_AnsibleLazyTemplateMixin._try_create({k: v for k, v in jinja_locals.items() if v is not missing}))

    if jinja_vars:
        layers.extend(_flatten_and_lazify_vars(jinja_vars))

    if jinja_globals and not shared:
        # Even though we don't currently support templating globals, it's easier to ensure that everything is template-able rather than trying to
        # pick apart the ChainMaps to enforce non-template-able globals, or to risk things that *should* be template-able not being lazified.
        layers.extend(_flatten_and_lazify_vars(jinja_globals))

    if not layers:
        # ensure we have at least one layer (which should be lazy), since _flatten_and_lazify_vars eliminates most empty layers
        layers.append(_AnsibleLazyTemplateMixin._try_create({}))

    # only return a ChainMap if we're combining layers, or we have none
    parent = layers[0] if len(layers) == 1 else ChainMap(*layers)

    # the `parent` cast is only to satisfy Jinja's overly-strict type hint
    return environment.context_class(environment, t.cast(dict, parent), template_name, blocks, globals=jinja_globals)
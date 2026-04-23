def list_summaries(logdir):
    """Read all summaries under the logdir into a `_SummaryFile`.

    Args:
      logdir: A path to a directory that contains zero or more event
        files, either as direct children or in transitive subdirectories.
        Summaries in these events must only contain old-style scalars,
        images, and histograms. Non-summary events, like `graph_def`s, are
        ignored.

    Returns:
      A `_SummaryFile` object reflecting all summaries written to any
      event files in the logdir or any of its descendant directories.

    Raises:
      ValueError: If an event file contains an summary of unexpected kind.
    """
    result = _SummaryFile()
    for dirpath, _, filenames in os.walk(logdir):
        for filename in filenames:
            if not filename.startswith("events.out."):
                continue
            path = os.path.join(dirpath, filename)
            for event in _SummaryIterator(path):
                if event.graph_def:
                    result.graph_defs.append(event.graph_def)
                if not event.summary:  # (e.g., it's a `graph_def` event)
                    continue
                for value in event.summary.value:
                    tag = value.tag
                    # Case on the `value` rather than the summary metadata
                    # because the Keras callback uses `summary_ops_v2` to emit
                    # old-style summaries. See b/124535134.
                    kind = value.WhichOneof("value")
                    container = {
                        "simple_value": result.scalars,
                        "image": result.images,
                        "histo": result.histograms,
                        "tensor": result.tensors,
                    }.get(kind)
                    if container is None:
                        raise ValueError(
                            "Unexpected summary kind %r in event file %s:\n%r"
                            % (kind, path, event)
                        )
                    elif kind == "tensor" and tag != "keras":
                        # Convert the tf2 summary proto to old style for type
                        # checking.
                        plugin_name = value.metadata.plugin_data.plugin_name
                        container = {
                            "images": result.images,
                            "histograms": result.histograms,
                            "scalars": result.scalars,
                        }.get(plugin_name)
                        if container is not None:
                            result.convert_from_v2_summary_proto = True
                        else:
                            container = result.tensors
                    container.add(_ObservedSummary(logdir=dirpath, tag=tag))
    return result
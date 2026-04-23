def generate_example_rst(example_case: ExportCase):
    """
    Generates the .rst files for all the examples in db/examples/
    """

    model = example_case.model

    tags = ", ".join(f":doc:`{tag} <{tag}>`" for tag in example_case.tags)

    source_file = (
        inspect.getfile(model.__class__)
        if isinstance(model, torch.nn.Module)
        else inspect.getfile(model)
    )
    with open(source_file) as file:
        source_code = file.read()
    source_code = source_code.replace("\n", "\n    ")
    splitted_source_code = re.split(r"@export_rewrite_case.*\n", source_code)

    if len(splitted_source_code) not in {1, 2}:
        raise AssertionError(
            f"more than one @export_rewrite_case decorator in {source_code}"
        )

    more_arguments = ""
    if example_case.example_kwargs:
        more_arguments += ", example_kwargs"
    if example_case.dynamic_shapes:
        more_arguments += ", dynamic_shapes=dynamic_shapes"

    # Generate contents of the .rst file
    title = f"{example_case.name}"
    doc_contents = f"""{title}
{"^" * (len(title))}

.. note::

    Tags: {tags}

    Support Level: {example_case.support_level.name}

Original source code:

.. code-block:: python

    {splitted_source_code[0]}

    torch.export.export(model, example_args{more_arguments})

Result:

.. code-block::

"""

    # Get resulting graph from dynamo trace
    try:
        exported_program = export(
            model,
            example_case.example_args,
            example_case.example_kwargs,
            dynamic_shapes=example_case.dynamic_shapes,
            strict=True,
        )
        graph_output = str(exported_program)
        graph_output = re.sub(r"        # File(.|\n)*?\n", "", graph_output)
        graph_output = graph_output.replace("\n", "\n    ")
        output = f"    {graph_output}"
    except torchdynamo.exc.Unsupported as e:
        output = "    Unsupported: " + str(e).split("\n")[0]
    except AssertionError as e:
        output = "    AssertionError: " + str(e).split("\n")[0]
    except RuntimeError as e:
        output = "    RuntimeError: " + str(e).split("\n")[0]

    doc_contents += output + "\n"

    if len(splitted_source_code) == 2:
        doc_contents += f"""\n
You can rewrite the example above to something like the following:

.. code-block:: python

{splitted_source_code[1]}

"""

    return doc_contents
def get_all_examples():
    """get_all_examples() -> str

    This function grabs (hopefully all) examples from the torch documentation
    strings and puts them in one nonsensical module returned as a string.
    """
    blocklist = {
        "_np",
        "_InputT",
    }

    example_file_lines = [
        "# mypy: allow-untyped-defs",
        "",
        "import math",
        "import io",
        "import itertools",
        "",
        "from typing import Any, ClassVar, Generic, List, Tuple, Union",
        "from typing_extensions import Literal, get_origin, TypeAlias",
        "T: TypeAlias = object",
        "",
        "import numpy",
        "",
        "import torch",
        "import torch.nn.functional as F",
        "",
        "from typing_extensions import ParamSpec as _ParamSpec",
        "ParamSpec = _ParamSpec",
        "",
        # for requires_grad_ example
        # NB: We are parsing this file as Python 2, so we must use
        # Python 2 type annotation syntax
        "def preprocess(inp):",
        "    # type: (torch.Tensor) -> torch.Tensor",
        "    return inp",
    ]

    for fname in dir(torch):
        fn = getattr(torch, fname)
        docstr = inspect.getdoc(fn)
        if docstr and fname not in blocklist:
            e = get_examples_from_docstring(docstr)
            if e:
                example_file_lines.append(f"\n\ndef example_torch_{fname}() -> None:")
                example_file_lines += e

    for fname in dir(torch.Tensor):
        fn = getattr(torch.Tensor, fname)
        docstr = inspect.getdoc(fn)
        if docstr and fname not in blocklist:
            e = get_examples_from_docstring(docstr)
            if e:
                example_file_lines.append(
                    f"\n\ndef example_torch_tensor_{fname}() -> None:"
                )
                example_file_lines += e

    return "\n".join(example_file_lines)
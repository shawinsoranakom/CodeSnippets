def set_submodule(
        self, target: str, module: "Module", strict: bool = False
    ) -> None:
        """
        Set the submodule given by ``target`` if it exists, otherwise throw an error.

        .. note::
            If ``strict`` is set to ``False`` (default), the method will replace an existing submodule
            or create a new submodule if the parent module exists. If ``strict`` is set to ``True``,
            the method will only attempt to replace an existing submodule and throw an error if
            the submodule does not exist.

        For example, let's say you have an ``nn.Module`` ``A`` that
        looks like this:

        .. code-block:: text

            A(
                (net_b): Module(
                    (net_c): Module(
                        (conv): Conv2d(3, 3, 3)
                    )
                    (linear): Linear(3, 3)
                )
            )

        (The diagram shows an ``nn.Module`` ``A``. ``A`` has a nested
        submodule ``net_b``, which itself has two submodules ``net_c``
        and ``linear``. ``net_c`` then has a submodule ``conv``.)

        To override the ``Conv2d`` with a new submodule ``Linear``, you
        could call ``set_submodule("net_b.net_c.conv", nn.Linear(1, 1))``
        where ``strict`` could be ``True`` or ``False``

        To add a new submodule ``Conv2d`` to the existing ``net_b`` module,
        you would call ``set_submodule("net_b.conv", nn.Conv2d(1, 1, 1))``.

        In the above if you set ``strict=True`` and call
        ``set_submodule("net_b.conv", nn.Conv2d(1, 1, 1), strict=True)``, an AttributeError
        will be raised because ``net_b`` does not have a submodule named ``conv``.

        Args:
            target: The fully-qualified string name of the submodule
                to look for. (See above example for how to specify a
                fully-qualified string.)
            module: The module to set the submodule to.
            strict: If ``False``, the method will replace an existing submodule
                or create a new submodule if the parent module exists. If ``True``,
                the method will only attempt to replace an existing submodule and throw an error
                if the submodule doesn't already exist.

        Raises:
            ValueError: If the ``target`` string is empty or if ``module`` is not an instance of ``nn.Module``.
            AttributeError: If at any point along the path resulting from
                the ``target`` string the (sub)path resolves to a non-existent
                attribute name or an object that is not an instance of ``nn.Module``.
        """
        if target == "":
            raise ValueError("Cannot set the submodule without a target name!")

        atoms: list[str] = target.split(".")
        if not isinstance(module, torch.nn.Module):
            raise ValueError(
                "`" + "module" + f"` is not an nn.Module, found {type(module)}"
            )
        if len(atoms) == 1:
            parent: torch.nn.Module = self
        else:
            parent_key = ".".join(atoms[:-1])
            parent = self.get_submodule(parent_key)

        if strict and not hasattr(parent, atoms[-1]):
            raise AttributeError(
                parent._get_name() + " has no attribute `" + atoms[-1] + "`"
            )
        if hasattr(parent, atoms[-1]):
            mod = getattr(parent, atoms[-1])
            if not isinstance(mod, torch.nn.Module):
                raise AttributeError("`" + atoms[-1] + "` is not an nn.Module")
        setattr(parent, atoms[-1], module)
def visit_Assign(self, node: ast.Assign) -> None:
        """
        Validate top-level calls to `EmbedManager.embed` to include the requested resources and collect them in `embeds`.

        All calls must be of the form `var = (embed.)EmbedManager.embed(...)`.
        Optional import-time aliases for the `embed` module or `EmbedManager` type are supported.

        The `embed` callsite requires exactly two inline literal string posargs; any other form will fail the module build.
        If the `package` argument starts with `.`, it is assumed to be a relative import path from the calling Python module.
        """
        if not isinstance(call := node.value, Call) or not isinstance(func := call.func, Attribute) or func.attr != 'embed':
            return  # bail - an assignment whose RHS is not a function call to (something).embed()

        match func.value:
            case Attribute(attr=self._embedmanager_type_name, value=Name(id=self._embed_module_name)):
                pass  # keep going - embed_module_or_alias.EmbedManagerOrAlias.embed()
            case Name(id=self._embedmanager_type_name):
                pass  # keep going - EmbedManagerOrAlias.embed()
            case _:
                return  # bail - an embed() call we're not interested in

        # origin-tag the args with this callsite location so a later failure can point here
        embed_origin = self._origin.replace(line_num=call.lineno, col_num=call.col_offset + 1)
        call_posargs: list[str] = [embed_origin.tag(a.value) for a in call.args if isinstance(a, Constant) and isinstance(a.value, str)]

        self._assert_embed(len(call_posargs) == len(call.args) == 2, message="Embed requires exactly two inline literal strings", node=call)
        self._assert_embed(not call.keywords, message="Embed does not support keyword args", node=call)

        if call_posargs[0].startswith('.'):
            # resolve relative anchor reference
            call_posargs[0] = embed_origin.tag(_importlib_util.resolve_name(call_posargs[0], self.module_fqn.rpartition('.')[0]))

        self.embeds.add(EmbeddedResource(*call_posargs))
def parse_parameter(self, line: str) -> None:
        assert self.function is not None

        if not self.expecting_parameters:
            fail('Encountered parameter line when not expecting '
                 f'parameters: {line}')

        match self.parameter_state:
            case ParamState.START | ParamState.REQUIRED:
                self.to_required()
            case ParamState.LEFT_SQUARE_BEFORE:
                self.parameter_state = ParamState.GROUP_BEFORE
            case ParamState.GROUP_BEFORE:
                if not self.group:
                    self.to_required()
            case ParamState.GROUP_AFTER | ParamState.OPTIONAL:
                pass
            case st:
                fail(f"Function {self.function.name} has an unsupported group configuration. (Unexpected state {st}.a)")

        # handle "as" for  parameters too
        c_name = None
        m = re.match(r'(?:\* *)?\w+( +as +(\w+))', line)
        if m:
            c_name = m[2]
            line = line[:m.start(1)] + line[m.end(1):]

        try:
            ast_input = f"def x({line}\n): pass"
            module = ast.parse(ast_input)
        except SyntaxError:
            fail(f"Function {self.function.name!r} has an invalid parameter declaration: {line!r}")

        function = module.body[0]
        assert isinstance(function, ast.FunctionDef)
        function_args = function.args

        if len(function_args.args) > 1:
            fail(f"Function {self.function.name!r} has an "
                 f"invalid parameter declaration (comma?): {line!r}")

        is_vararg = is_var_keyword = False
        if function_args.vararg:
            self.check_previous_star()
            self.check_remaining_star()
            is_vararg = True
            parameter = function_args.vararg
        elif function_args.kwarg:
            # If the existing parameters are all positional only or ``*args``
            # (var-positional), then we allow ``**kwds`` (var-keyword).
            # Currently, pos-or-keyword or keyword-only arguments are not
            # allowed with the ``**kwds`` converter.
            has_non_positional_param = any(
                p.is_positional_or_keyword() or p.is_keyword_only()
                for p in self.function.parameters.values()
            )
            if has_non_positional_param:
                fail(f"Function {self.function.name!r} has an "
                     f"invalid parameter declaration (**kwargs?): {line!r}")
            is_var_keyword = True
            parameter = function_args.kwarg
        else:
            parameter = function_args.args[0]

        parameter_name = parameter.arg
        name, legacy, kwargs = self.parse_converter(parameter.annotation)
        if is_vararg:
            name = f'varpos_{name}'
        elif is_var_keyword:
            name = f'var_keyword_{name}'

        value: object
        has_c_default = 'c_default' in kwargs
        if not function_args.defaults:
            value = unspecified
            if (not is_vararg and not is_var_keyword
                    and self.parameter_state is ParamState.OPTIONAL):
                fail(f"Can't have a parameter without a default ({parameter_name!r}) "
                     "after a parameter with a default!")
            if 'py_default' in kwargs:
                fail("You can't specify py_default without specifying a default value!")
            if has_c_default:
                fail("You can't specify c_default without specifying a default value!")
        else:
            expr = function_args.defaults[0]
            default = ast_input[expr.col_offset: expr.end_col_offset].strip()

            if self.parameter_state is ParamState.REQUIRED:
                self.parameter_state = ParamState.OPTIONAL
            bad = False
            try:
                if not has_c_default:
                    # we can only represent very simple data values in C.
                    # detect whether default is okay, via a denylist
                    # of disallowed ast nodes.
                    class DetectBadNodes(ast.NodeVisitor):
                        bad = False
                        def bad_node(self, node: ast.AST) -> None:
                            self.bad = True

                        # inline function call
                        visit_Call = bad_node
                        # inline if statement ("x = 3 if y else z")
                        visit_IfExp = bad_node

                        # comprehensions and generator expressions
                        visit_ListComp = visit_SetComp = bad_node
                        visit_DictComp = visit_GeneratorExp = bad_node

                        # literals for advanced types
                        visit_Dict = visit_Set = bad_node
                        visit_List = visit_Tuple = bad_node

                        # "starred": "a = [1, 2, 3]; *a"
                        visit_Starred = bad_node

                    denylist = DetectBadNodes()
                    denylist.visit(expr)
                    bad = denylist.bad
                else:
                    # if they specify a c_default, we can be more lenient about the default value.
                    # but at least make an attempt at ensuring it's a valid expression.
                    code = compile(ast.Expression(expr), '<expr>', 'eval')
                    try:
                        value = eval(code)
                    except NameError:
                        pass # probably a named constant
                    except Exception as e:
                        fail("Malformed expression given as default value "
                             f"{default!r} caused {e!r}")
                    else:
                        if value is unspecified:
                            fail("'unspecified' is not a legal default value!")
                if bad:
                    fail(f"Unsupported expression as default value: {default!r}")

                # mild hack: explicitly support NULL as a default value
                if isinstance(expr, ast.Name) and expr.id == 'NULL':
                    value = NULL
                    py_default = '<unrepresentable>'
                elif (isinstance(expr, ast.BinOp) or
                    (isinstance(expr, ast.UnaryOp) and
                     not (isinstance(expr.operand, ast.Constant) and
                          type(expr.operand.value) in {int, float, complex})
                    )):
                    if not has_c_default:
                        fail(f"When you specify an expression ({default!r}) "
                             f"as your default value, "
                             f"you MUST specify a valid c_default.",
                             ast.dump(expr))
                    py_default = default
                    value = unknown
                elif isinstance(expr, ast.Attribute):
                    a = []
                    n: ast.expr | ast.Attribute = expr
                    while isinstance(n, ast.Attribute):
                        a.append(n.attr)
                        n = n.value
                    if not isinstance(n, ast.Name):
                        fail(f"Unsupported default value {default!r} "
                             "(looked like a Python constant)")
                    a.append(n.id)
                    py_default = ".".join(reversed(a))

                    if not has_c_default:
                        fail(f"When you specify a named constant ({py_default!r}) "
                             "as your default value, "
                             "you MUST specify a valid c_default.")

                    try:
                        value = eval(py_default)
                    except NameError:
                        value = unknown
                else:
                    value = ast.literal_eval(expr)
                    py_default = repr(value)

            except (ValueError, AttributeError):
                value = unknown
                py_default = default
                if not has_c_default:
                    fail("When you specify a named constant "
                         f"({py_default!r}) as your default value, "
                         "you MUST specify a valid c_default.")

            kwargs.setdefault('py_default', py_default)

        dict = legacy_converters if legacy else converters
        legacy_str = "legacy " if legacy else ""
        if name not in dict:
            fail(f'{name!r} is not a valid {legacy_str}converter')
        # if you use a c_name for the parameter, we just give that name to the converter
        # but the parameter object gets the python name
        converter = dict[name](c_name or parameter_name, parameter_name, self.function, value, **kwargs)

        kind: inspect._ParameterKind
        if is_vararg:
            kind = inspect.Parameter.VAR_POSITIONAL
        elif is_var_keyword:
            kind = inspect.Parameter.VAR_KEYWORD
        elif self.keyword_only:
            kind = inspect.Parameter.KEYWORD_ONLY
        else:
            kind = inspect.Parameter.POSITIONAL_OR_KEYWORD

        if isinstance(converter, self_converter):
            if len(self.function.parameters) == 1:
                if self.group:
                    fail("A 'self' parameter cannot be in an optional group.")
                assert self.parameter_state is ParamState.REQUIRED
                assert value is unspecified
                kind = inspect.Parameter.POSITIONAL_ONLY
                self.parameter_state = ParamState.START
                self.function.parameters.clear()
            else:
                fail("A 'self' parameter, if specified, must be the "
                     "very first thing in the parameter block.")

        if isinstance(converter, defining_class_converter):
            _lp = len(self.function.parameters)
            if _lp == 1:
                if self.group:
                    fail("A 'defining_class' parameter cannot be in an optional group.")
                if self.function.cls is None:
                    fail("A 'defining_class' parameter cannot be defined at module level.")
                assert self.parameter_state is ParamState.REQUIRED
                assert value is unspecified
                kind = inspect.Parameter.POSITIONAL_ONLY
            else:
                fail("A 'defining_class' parameter, if specified, must either "
                     "be the first thing in the parameter block, or come just "
                     "after 'self'.")


        p = Parameter(parameter_name, kind, function=self.function,
                      converter=converter, default=value, group=self.group,
                      deprecated_positional=self.deprecated_positional)

        names = [k.name for k in self.function.parameters.values()]
        if parameter_name in names[1:]:
            fail(f"You can't have two parameters named {parameter_name!r}!")
        elif names and parameter_name == names[0] and c_name is None:
            fail(f"Parameter {parameter_name!r} requires a custom C name")

        key = f"{parameter_name}_as_{c_name}" if c_name else parameter_name
        self.function.parameters[key] = p

        if is_vararg:
            self.keyword_only = True
        if is_var_keyword:
            self.expecting_parameters = False
def _render_iterall(self, view_ref, method, values, directive='render') -> Iterator[str]:
        """ Iterate over the generator method.
            Generator elements are a str
        """
        root_values = values['__qweb_root_values']
        loaded_functions = self.env.context['__qweb_loaded_functions']

        params = QwebCallParameters(
            context={},
            view_ref=view_ref,
            method=method,
            values=None,
            scope=False,
            directive=directive,
            path_xml=None,
        )
        stack = [QwebStackFrame(params, self, iter([params]), values, None)]

        try:
            while stack:
                if len(stack) > 50:
                    raise RecursionError('Qweb template infinite recursion')  # noqa: TRY301

                frame = stack[-1]

                # traverse the iterator
                for item in frame.iterator:
                    # To debug the rendering step by step you can log the (len(stack) * '  ', repr(item))
                    if isinstance(item, str):
                        yield item
                        continue

                    # use QwebContent params or return already evaluated QwebContent
                    if is_content := isinstance(item, QwebContent):
                        if item.html is not None:
                            yield item.html
                            continue
                        params = item.params__

                    else:  # isinstance(item, QwebCallParameters)
                        params = item

                    # add new QwebStackFrame from QwebCallParameters
                    values = frame.values
                    irQweb = frame.irQweb

                    # Use the current directive context
                    if params.context:
                        irQweb = irQweb.with_context(**params.context)

                    render_template = loaded_functions.get(params.method)

                    # Fetch the compiled function and template options
                    if not render_template:
                        template_functions, def_name, options = irQweb._compile(params.view_ref)
                        loaded_functions.update(template_functions)
                        render_template = template_functions[params.method or def_name]
                    else:
                        options = irQweb._compile(params.view_ref)[2]

                    # Apply a new scope if needed
                    if params.scope:
                        if params.scope == 'root':
                            values = root_values
                        values = values.copy()

                    # Update values with default values
                    if params.values:
                        values.update(params.values)

                    iterator = iter([])
                    try:
                        # Create the iterator from the template
                        iterator = render_template(irQweb, values)
                    finally:
                        if is_content and self.env.context['_qweb_error_path_xml'][1]:
                            # add a stack frame to log a complete error with the path when compile the template
                            logParams = QwebCallParameters(*(params[0:-1] + (tuple(self.env.context['_qweb_error_path_xml']),)))
                            stack.append(QwebStackFrame(logParams, irQweb, [], values, options))
                        stack.append(QwebStackFrame(params, irQweb, iterator, values, options))
                    break

                else:
                    stack.pop()

        except (TransactionRollbackError, ReadOnlySqlTransaction):
            raise

        except Exception as error:
            qweb_error_info = self._get_error_info(error, stack, stack[-1])
            if qweb_error_info.template is None and qweb_error_info.ref is None:
                qweb_error_info.ref = view_ref

            if hasattr(error, 'qweb'):
                if qweb_error_info.source:
                    error.qweb.source = qweb_error_info.source + error.qweb.source
                if not error.qweb.ref and frame.params.view_ref:
                    error.qweb.ref = frame.params.view_ref
                qweb_error_info = error.qweb
            elif not isinstance(error, UserError):
                # If is not an odoo Exception check if the current error is raise from
                # IrQweb (models or computed code). In this case, convert it into an QWebError.
                isQweb = False

                trace = error.__traceback__
                tb_frames = [trace.tb_frame]
                while trace.tb_next is not None:
                    trace = trace.tb_next
                    tb_frames.append(trace.tb_frame)
                for tb_frame in tb_frames[::-1]:
                    if tb_frame.f_globals.get('__name__') == __name__ or (
                        isinstance(tb_frame.f_locals.get('self'), models.AbstractModel)
                        and tb_frame.f_locals['self']._name == self._name
                    ):
                        isQweb = True
                        break
                    if any(path in tb_frame.f_code.co_filename for path in tools.config['addons_path']):
                        break

                if isQweb:
                    raise QWebError(qweb_error_info) from error

            error.qweb = qweb_error_info
            raise
def _finalize_top_level_template_result(
        variable: t.Any,
        options: TemplateOptions,
        template_result: t.Any,
        is_expression: bool = False,
        stop_on_container: bool = False,
    ) -> t.Any:
        """
        This method must be called for expressions and top-level templates to recursively finalize the result.
        This renders any embedded templates and triggers `Marker` and omit behaviors.
        """
        try:
            if template_result is Omit:
                # When the template result is Omit, raise an AnsibleValueOmittedError if value_for_omit is Omit, otherwise return value_for_omit.
                # Other occurrences of Omit will simply drop out of containers during _finalize_template_result.
                if options.value_for_omit is Omit:
                    raise AnsibleValueOmittedError()

                return options.value_for_omit  # trust that value_for_omit is an allowed type

            if stop_on_container and type(template_result) in AnsibleTaggedObject._collection_types:
                # Use of stop_on_container implies the caller will perform necessary checks on values,
                # most likely by passing them back into the templating system.
                try:
                    return template_result._non_lazy_copy()
                except AttributeError:
                    return template_result  # non-lazy containers are returned as-is

            return _finalize_template_result(template_result, FinalizeMode.TOP_LEVEL)
        except TemplateEncountered:
            raise
        except Exception as ex:
            raise_from: BaseException

            if isinstance(ex, MarkerError):
                exception_to_raise = ex.source._as_exception()

                # MarkerError is never suitable for use as the cause of another exception, it is merely a raiseable container for the source marker
                # used for flow control (so its stack trace is rarely useful). However, if the source derives from a ExceptionMarker, its contained
                # exception (previously raised) should be used as the cause. Other sources do not contain exceptions, so cannot provide a cause.
                raise_from = exception_to_raise if isinstance(ex.source, ExceptionMarker) else None
            else:
                exception_to_raise = ex
                raise_from = ex

            exception_to_raise = create_template_error(exception_to_raise, variable, is_expression)

            if exception_to_raise is ex:
                raise  # when the exception to raise is the active exception, just re-raise it

            if exception_to_raise is raise_from:
                raise_from = exception_to_raise.__cause__  # preserve the exception's cause, if any, otherwise no cause will be used

            raise exception_to_raise from raise_from
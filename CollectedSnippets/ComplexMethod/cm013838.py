def is_int_specialization_case(value: Any, source: Any) -> bool:
    from .source import is_from_defaults

    return not TracingContext.get().force_unspec_int_unbacked_size_like and (
        # Assume integers from global variables want to be specialized
        not source.guard_source.is_local()
        # Assume that integers that came from NN modules want to be
        # specialized (as we don't expect users to be changing the
        # NN modules on the fly), unless explicitly disabled
        or (
            source.guard_source.is_specialized_nn_module()
            and not config.allow_unspec_int_on_nn_module
        )
        or (
            source.guard_source.is_unspecialized_builtin_nn_module()
            and not config.allow_unspec_int_on_nn_module
        )
        or (
            source.guard_source.is_unspecialized_nn_module()
            and not config.allow_unspec_int_on_nn_module
        )
        or is_from_defaults(source)
        # TODO: Delete this condition when rollout is done.  NB: this
        # condition never evaluates True in open source
        or (
            not justknobs_check("pytorch/dynamo:enable_unspecialize_zero_one_plain_int")
            and value in common_constants()
        )
    )
def _activation_post_process_satisfies_dtype_config_constraints(
        activation_post_process: ObserverBase | FakeQuantizeBase,
        dtype_with_constraints: DTypeWithConstraints,
        debug_string: str,
    ) -> bool:
        observer = _get_observer_from_activation_post_process(activation_post_process)
        app_quant_min = getattr(observer, "quant_min", None)
        app_quant_max = getattr(observer, "quant_max", None)
        # TODO: for now, just use the existing eps value as scale_min. In the future, we should
        # resolve the differences between the two, either by renaming eps or some other way
        app_scale_min = getattr(observer, "eps", None)
        backend_quant_min = dtype_with_constraints.quant_min_lower_bound
        backend_quant_max = dtype_with_constraints.quant_max_upper_bound
        backend_scale_min = dtype_with_constraints.scale_min_lower_bound
        backend_scale_exact_match = dtype_with_constraints.scale_exact_match
        backend_zero_point_exact_match = dtype_with_constraints.zero_point_exact_match
        # check quantization ranges
        if backend_quant_min is not None and backend_quant_max is not None:
            if app_quant_min is None or app_quant_max is None:
                warnings.warn(
                    f"QConfig {debug_string} must specify 'quant_min' and 'quant_max', ignoring {qconfig}",
                    stacklevel=2,
                )
                return False
            elif app_quant_min < backend_quant_min or app_quant_max > backend_quant_max:
                warnings.warn(
                    f"QConfig {debug_string} quantization range must fall within the backend's:\n"
                    f"QConfig range = ({app_quant_min}, {app_quant_max}), "
                    f"BackendConfig range = ({backend_quant_min}, {backend_quant_max}), "
                    f"ignoring {qconfig}",
                    stacklevel=2,
                )
                return False
        # check scale min
        if backend_scale_min is not None:
            if app_scale_min is None:
                warnings.warn(
                    f"QConfig {debug_string} must specify 'eps', ignoring {qconfig}",
                    stacklevel=2,
                )
                return False
            if app_scale_min < backend_scale_min:
                warnings.warn(
                    f"QConfig {debug_string} eps ({app_scale_min}) must be greater than or equal to "
                    f"the backend's min scale value ({backend_scale_min}), ignoring {qconfig}",
                    stacklevel=2,
                )
                return False
        # check fixed scale and zero point
        if (
            backend_scale_exact_match is not None
            and backend_zero_point_exact_match is not None
        ):
            # For tests only, accept the following qconfigs for now
            # TODO: handle fp16 qconfigs properly
            for accepted_qconfig in [float16_static_qconfig, float16_dynamic_qconfig]:
                if qconfig_equals(qconfig, accepted_qconfig):
                    return True
            suggestion_str = (
                "Please use torch.ao.quantization.get_default_qconfig_mapping or "
                "torch.ao.quantization.get_default_qat_qconfig_mapping. Example:\n"
                '    qconfig_mapping = get_default_qconfig_mapping("fbgemm")\n'
                "    model = prepare_fx(model, qconfig_mapping, example_inputs)"
            )
            if not isinstance(
                activation_post_process, FixedQParamsObserver
            ) and not isinstance(activation_post_process, FixedQParamsFakeQuantize):
                warnings.warn(
                    f"QConfig must specify a FixedQParamsObserver or a FixedQParamsFakeQuantize "
                    f"for fixed qparams ops, ignoring {qconfig}.\n{suggestion_str}",
                    stacklevel=2,
                )
                return False
            if (
                observer.scale != backend_scale_exact_match
                or observer.zero_point != backend_zero_point_exact_match
            ):
                warnings.warn(
                    f"QConfig fixed scale ({observer.scale}) and zero point ({observer.zero_point}) "
                    f"do not match the backend's ({backend_scale_exact_match} and {backend_zero_point_exact_match}), "
                    f"ignoring {qconfig}.\n{suggestion_str}",
                    stacklevel=2,
                )
                return False
        return True
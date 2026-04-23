def generate_service_api(output, service: ServiceModel, doc=True):
    service_name = service.service_name.replace("-", "_")
    class_name = service_name + "_api"
    class_name = snake_to_camel_case(class_name)

    output.write(f"class {class_name}:\n")
    output.write("\n")
    output.write(f'    service: str = "{service.service_name}"\n')
    output.write(f'    version: str = "{service.api_version}"\n')
    for op_name in service.operation_names:
        operation: OperationModel = service.operation_model(op_name)

        fn_name = camel_to_snake_case(op_name)

        if operation.output_shape:
            output_shape = to_valid_python_name(operation.output_shape.name)
        else:
            output_shape = "None"

        output.write("\n")
        parameters = OrderedDict()
        param_shapes = OrderedDict()

        if input_shape := operation.input_shape:
            members = list(input_shape.members)

            streaming_payload_member = None
            if operation.has_streaming_input:
                streaming_payload_member = operation.input_shape.serialization.get("payload")

            for m in input_shape.required_members:
                members.remove(m)
                m_shape = input_shape.members[m]
                type_name = to_valid_python_name(m_shape.name)
                if m == streaming_payload_member:
                    type_name = f"IO[{type_name}]"
                parameters[xform_name(m)] = type_name
                param_shapes[xform_name(m)] = m_shape

            for m in members:
                m_shape = input_shape.members[m]
                param_shapes[xform_name(m)] = m_shape
                type_name = to_valid_python_name(m_shape.name)
                if m == streaming_payload_member:
                    type_name = f"IO[{type_name}]"
                parameters[xform_name(m)] = f"{type_name} | None = None"

        if any(map(is_bad_param_name, parameters.keys())):
            # if we cannot render the parameter name, don't expand the parameters in the handler
            param_list = f"request: {to_valid_python_name(input_shape.name)}" if input_shape else ""
            output.write(f'    @handler("{operation.name}", expand=False)\n')
        else:
            param_list = ", ".join([f"{k}: {v}" for k, v in parameters.items()])
            output.write(f'    @handler("{operation.name}")\n')

        # add the **kwargs in the end
        if param_list:
            param_list += ", **kwargs"
        else:
            param_list = "**kwargs"

        output.write(
            f"    def {fn_name}(self, context: RequestContext, {param_list}) -> {output_shape}:\n"
        )

        # convert html documentation to rst and print it into to the signature
        if doc:
            html = operation.documentation
            rst = html_to_rst(html)
            output.write('        """')
            output.write(f"{rst}\n")
            output.write("\n")

            # parameters
            for param_name, shape in param_shapes.items():
                # FIXME: this doesn't work properly
                rst = html_to_rst(shape.documentation)
                rst = rst.strip().split(".")[0] + "."
                output.write(f":param {param_name}: {rst}\n")

            # return value
            if operation.output_shape:
                output.write(f":returns: {to_valid_python_name(operation.output_shape.name)}\n")

            # errors
            for error in operation.error_shapes:
                output.write(f":raises {to_valid_python_name(error.name)}:\n")

            output.write('        """\n')

        output.write("        raise NotImplementedError\n")
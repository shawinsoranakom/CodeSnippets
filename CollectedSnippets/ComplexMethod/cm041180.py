def _print_as_class(self, output, base: str, doc=True, quote_types=False):
        output.write(f"class {to_valid_python_name(self.shape.name)}({base}):\n")

        q = '"' if quote_types else ""

        if doc:
            self.print_shape_doc(output, self.shape)

        if self.is_exception:
            error_spec = self.shape.metadata.get("error", {})
            output.write(f'    code: str = "{error_spec.get("code", self.shape.name)}"\n')
            output.write(f"    sender_fault: bool = {error_spec.get('senderFault', False)}\n")
            output.write(f"    status_code: int = {error_spec.get('httpStatusCode', 400)}\n")
        elif not self.shape.members:
            output.write("    pass\n")

        # Avoid generating members for the common error members:
        # - The message will always be the exception message (first argument of the exception class init)
        # - The code is already set above
        # - The type is the sender_fault which is already set above
        remaining_members = {
            k: v
            for k, v in self.shape.members.items()
            if not self.is_exception or k.lower() not in ["message", "code"]
        }

        # render any streaming payload first
        if self.is_request and self.request_operation.has_streaming_input:
            member: str = self.request_operation.input_shape.serialization.get("payload")
            shape: Shape = self.request_operation.get_streaming_input()
            if member in self.shape.required_members:
                output.write(f"    {member}: IO[{q}{to_valid_python_name(shape.name)}{q}]\n")
            else:
                output.write(f"    {member}: {q}IO[{to_valid_python_name(shape.name)}] | None{q}\n")
            del remaining_members[member]
        # render the streaming payload first
        if self.is_response and self.response_operation.has_streaming_output:
            member: str = self.response_operation.output_shape.serialization.get("payload")
            shape: Shape = self.response_operation.get_streaming_output()
            shape_name = to_valid_python_name(shape.name)
            if member in self.shape.required_members:
                output.write(
                    f"    {member}: {q}{shape_name} | IO[{shape_name}] | Iterable[{shape_name}]{q}\n"
                )
            else:
                output.write(
                    f"    {member}: {q}{shape_name} | IO[{shape_name}] | Iterable[{shape_name}] | None{q}\n"
                )
            del remaining_members[member]

        for k, v in remaining_members.items():
            shape_name = to_valid_python_name(v.name)
            if k in self.shape.required_members:
                if v.serialization.get("eventstream"):
                    output.write(f"    {k}: Iterator[{q}{shape_name}{q}]\n")
                else:
                    output.write(f"    {k}: {q}{shape_name}{q}\n")
            else:
                if v.serialization.get("eventstream"):
                    output.write(f"    {k}: Iterator[{q}{shape_name}{q}]\n")
                else:
                    output.write(f"    {k}: {q}{shape_name} | None{q}\n")
def shape_inference(self, func: NativeFunction, schema: LazyIrSchema) -> str:
        metadata = self.backend_index.get_kernel(func)
        if metadata is None:
            raise AssertionError(f"No kernel metadata found for {func.func.name}")
        all_args = schema.filtered_args()
        returns_length = len(schema.returns)
        # call the meta kernel if it exists, to compute output shape/dtype for our IR
        # Note [Generated LTC Shape Functions]
        # LTC uses meta tensors from core to do shape inference when possible, and otherwise
        # we generate a shape function declaration that needs to be manually implemented.
        # How do we detect which ops are eligible to use meta tensors?
        # In general we should be able to use meta tensors not just on structured operators,
        # but also on composite operators that are implemented in terms of structured kernels.
        # We don't currently have a way of knowing at codegen time which ops are implemented that way.
        # This is the case for all view and view_copy operators however, so we're going to
        # use them specifically for all of the view_copy ops (instead of manually writing shape rules for all of them).
        is_view_copy_op = "view_copy" in func.tags
        is_structured = func.structured or func.structured_delegate is not None
        if is_structured or is_view_copy_op:
            meta_out = """
std::vector<torch::lazy::Shape> shapes{torch::lazy::Shape(out_meta.scalar_type(), out_meta.sizes().vec())};"""
            if returns_length > 1:

                def this_shape(i: int) -> str:
                    return f"torch::lazy::Shape(std::get<{i}>(out_meta).scalar_type(), std::get<{i}>(out_meta).sizes().vec())"

                shapes_str = ",".join([this_shape(i) for i in range(returns_length)])
                meta_out = "std::vector<torch::lazy::Shape> shapes{" + shapes_str + "};"

            # Convert tensor args to the meta device and call it.
            # (We can't pass in the input tensors directly, because they are "functional wrappers".
            # If any of the meta kernels call a tensor op and redispatch, we don't want to hit the functionalize kernels.)
            # Even at::meta:: functions might redispatch, e.g. if they call into view ops.
            dispatcher_sig = DispatcherSignature.from_schema(func.func)
            meta_conversion_str, meta_call_ctx = convert_to_meta_tensors(dispatcher_sig)
            meta_call_args = [
                e.expr
                for e in translate(
                    meta_call_ctx, dispatcher_sig.arguments(), method=False
                )
            ]
            if is_view_copy_op:
                # view_copy ops always have a CompositeExplicitAutogradNonFunctional kernel
                if not func.has_composite_explicit_autograd_non_functional_kernel:
                    raise AssertionError(
                        f"view_copy op {func.func.name} must have "
                        "CompositeExplicitAutogradNonFunctional kernel"
                    )
                dispatch_ns = "compositeexplicitautogradnonfunctional"
            else:
                dispatch_ns = "meta"
            aten_name = schema.aten_name
            # TODO: this is trolling
            if func.func.has_symint() and metadata.supports_symint():
                aten_name += "_symint"
            shape_str = f"""\
        {meta_conversion_str}
        auto out_meta = at::{dispatch_ns}::{aten_name}({", ".join(meta_call_args)});
        {meta_out}"""
        else:
            shape_sig = ComputeShapeSignature(
                metadata.kernel, func, symint=metadata.supports_symint()
            )
            shape_str = f"""
            auto shapes = {shape_sig.shape_call};"""

        shape_str += f"""
            TORCH_INTERNAL_ASSERT(shapes.size() == {returns_length});"""

        # Calculating which dimensions are symbolic
        func_schema_str = "aten::" + str(func.func)
        shape_str += f"""
            if(torch::lazy::symbolicShapeEnabled()){{
                std::vector<torch::jit::IValue> inputs = {{ {", ".join(str(a.name) for a in all_args)} }};
                const char* schema_str = "{func_schema_str}";
                applySymbolicShapesOnLT(schema_str, inputs, shapes);
            }}
        """
        return shape_str
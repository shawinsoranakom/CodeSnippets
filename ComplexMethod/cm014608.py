def gen_one(self, f: NativeFunction) -> str | None:
        if f.manual_kernel_registration:
            raise AssertionError(
                f"Function {f.func.name} has manual_kernel_registration=True"
            )

        if (
            self.target is Target.REGISTRATION
            and not self.selector.is_native_function_selected(f)
        ):
            return None

        # TODO: Now, there is something interesting going on here.  In the code below,
        # we generate CompositeExplicitAutogradNonFunctional implementations of functional and inplace
        # based on the out implementation.  But in fact, out is definable by
        # functional too (just not very efficiently), and this is honestly the
        # MORE likely situation for a backend implementer.  How do we pick?
        # Well, taking a page from Haskell type classes and default methods,
        # we could conceivably register a circular definition (out in terms
        # of functional, and functional in terms of out) and just require
        # someone to implement one or the other.  We'd have to do a little bit
        # of work to not register one of these "weak" definitions unless there
        # is a strong definition somewhere in the DAG!  So it's not implemented yet.
        if (
            self.backend_index.dispatch_key
            == DispatchKey.CompositeExplicitAutogradNonFunctional
            and f.func.kind() is SchemaKind.out
        ):
            # Never generate a default implementation for out, that's what you
            # have to define as a backend implementer
            return None

        # Note [Direct dispatch bindings]
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Signature of the non-dispatched function we'll expose in a header
        # (e.g., at::cpu::add).  We don't generate methods (TODO: do this
        # when CPUTensor class is a thing); nor do we generate fallback
        # bindings for manual_cpp_binding functions.
        cpp_sig_group = CppSignatureGroup.from_native_function(
            f, method=False, fallback_binding=False
        )

        # Signature of the wrapper function we'll register to the dispatcher
        kern = self.backend_index.get_kernel(f)
        sig = NativeSignature(
            f.func,
            prefix=f"wrapper_{self.backend_index.dispatch_key}_",
            symint=kern is not None and kern.supports_symint(),
        )

        if self.target is Target.NAMESPACED_DECLARATION:
            result = ""
            for cpp_sig in cpp_sig_group.signatures(symint=self.symint):
                result += f"TORCH_API {cpp_sig.decl()};\n"
            return result

        elif self.target is Target.NAMESPACED_DEFINITION:

            def generate_defn(cpp_sig: CppSignature) -> str:
                return f"""
{cpp_sig.defn()} {{
return {sig.name()}({", ".join(e.expr for e in translate(cpp_sig.arguments(), sig.arguments()))});
}}
"""

            result = ""
            for cpp_sig in cpp_sig_group.signatures(symint=self.symint):
                result += generate_defn(cpp_sig)
            return result

        elif self.target is Target.ANONYMOUS_DEFINITION:
            k = f.func.kind()

            # Construct the body of the wrapper function with signature sig
            sig_body = []
            # We'll use context to keep track of any variables we've brought
            # into scope while generating code
            context: list[Binding | Expr] = list(sig.arguments())

            # Initialize the class corresponding to this structured
            # operator; feeding it the output argument(s) if it is known
            if self.backend_index.dispatch_key is DispatchKey.Meta:
                class_name = f"structured_{meta.name(self.g)}_meta_{k.name}"
                parent_class = f"at::meta::structured_{meta.name(self.g)}"
            elif (
                self.backend_index.dispatch_key
                is DispatchKey.CompositeExplicitAutogradNonFunctional
            ):
                # TODO: dedup this branch
                class_name = f"structured_{meta.name(self.g)}_default_backend_{k.name}"
                parent_class = f"at::meta::structured_{meta.name(self.g)}"
            else:
                metadata = self.backend_index.get_kernel(self.g)
                if metadata is None:
                    raise AssertionError(
                        f"No kernel metadata found for {self.g.functional.func.name}"
                    )
                class_name = f"structured_{metadata.kernel}_{k.name}"
                parent_class = f"{metadata.cpp_namespace}::structured_{metadata.kernel}"

            if self.backend_index.device_guard:
                device_check_args = itertools.chain(
                    f.func.arguments.out, f.func.arguments.flat_positional
                )
                sig_body.append(
                    RegisterDispatchKey.gen_device_check(
                        f.device_check, list(device_check_args), sig.name()
                    )
                )

            if k is SchemaKind.functional:
                sig_body.append(f"{class_name} op;")
            elif k is SchemaKind.inplace:
                sig_body.append(f"{class_name} op(self);")
            elif k is SchemaKind.out:
                out_args_str = ", ".join(a.name for a in f.func.arguments.out)
                sig_body.append(f"{class_name} op({out_args_str});")

            # Translate the input native arguments into structured
            # arguments for the meta call
            meta_exprs = ", ".join(
                e.expr
                for e in translate(
                    context, structured.meta_arguments(self.g), method=False
                )
            )

            if self.g.out.precomputed:
                # If this function group has precomputed elements, the meta function
                # returns a struct containing them which must be saved so that it
                # can be unpacked when generating code to call the impl.
                sig_body.append(f"auto precompute = op.meta({meta_exprs});")

                # Put all of the contents of the precompute struct into the context
                # so that translate will be able to return the correct args for the
                # call to the impl.
                precomputed_values = [
                    *self.g.out.precomputed.replace.values(),
                    self.g.out.precomputed.add,
                ]
                for precomputed_elems in precomputed_values:
                    context.extend(
                        Expr(
                            expr=f"precompute.{arg.name}",
                            type=structured.argument_type(arg, binds=arg.name),
                        )
                        for arg in precomputed_elems
                    )

                # Add a use of the precompute struct so FB internal compilers don't
                # complain that there is an unused variable.
                sig_body.append("(void)precompute;")
            else:
                sig_body.append(f"op.meta({meta_exprs});")

            # After running meta, op.outputs_ is guaranteed to be valid;
            # add it to the context
            out_args = structured.out_arguments(self.g)
            for i, out_arg in enumerate(out_args):
                if ConstRefCType(BaseCType(tensorT)) != out_arg.nctype.type:
                    raise AssertionError(
                        f"Expected out_arg type to be ConstRefCType(BaseCType(tensorT)), "
                        f"got {out_arg.nctype.type}"
                    )

                if k is SchemaKind.out:
                    expr = f"op.maybe_get_output({i})"
                else:
                    expr = f"op.outputs_[{i}]"

                context.append(
                    Expr(
                        expr=expr,
                        # TODO: Stop hardcoding that the output type is a Tensor.  Note
                        # that for the codegen here this is fine because outputs_ is
                        # hardcoded to be tensor already
                        type=NamedCType(
                            out_arg.nctype.name, MutRefCType(BaseCType(tensorT))
                        ),
                    )
                )

            # With the expanded context, do the impl call (if not a meta
            # function)
            if (
                self.backend_index.dispatch_key
                == DispatchKey.CompositeExplicitAutogradNonFunctional
            ):
                # TODO: https://github.com/pytorch/pytorch/issues/53023
                out_sig_group = CppSignatureGroup.from_native_function(
                    self.g.out, method=False, fallback_binding=f.manual_cpp_binding
                )
                out_sig = out_sig_group.most_faithful_signature()
                api_name = out_sig.name()
                out_exprs = ", ".join(
                    e.expr
                    for e in translate(context, out_sig.arguments(), method=False)
                )
                # TODO: I think this means structured won't work with method
                # only functions (but maybe you're saved by faithful? iunno.)
                # NB: Originally I wrote this as an at::redispatch call, but
                # I got in trouble because that meant I needed a DispatchKeySet
                # in the wrapper function, which meant I needed a DispatchKeySet
                # in the DispatchKeyFunctions declarations, but the defined API
                # there does NOT permit a dispatch key set.  I think you can
                # probably unwind this by calling some function to do the TLS
                # fetch and get the DispatchKeySet when you don't have it, but
                # I didn't do it for this version
                sig_body.append(f"at::{api_name}({out_exprs});")
            elif self.backend_index.dispatch_key != DispatchKey.Meta:
                impl_exprs = ", ".join(
                    e.expr
                    for e in translate(
                        context, structured.impl_arguments(self.g), method=False
                    )
                )
                sig_body.append(f"op.impl({impl_exprs});")

            # Go over each output, and check if there is a proxy created for it.
            # If so, copy it over to the original output.
            if k is SchemaKind.out or k is SchemaKind.inplace:
                for i in range(len(f.func.returns)):
                    sig_body.append(
                        f"if (op.proxy_outputs_[{i}].has_value()) op.outputs_[{i}].get().copy_(*op.proxy_outputs_[{i}]);"
                    )

            # Destructively return the final tensors
            # TODO: Do this in translate instead
            if k is SchemaKind.functional:
                if len(f.func.returns) == 1:
                    ret_expr = "std::move(op.outputs_[0])"  # small optimization
                else:
                    moved = ", ".join(
                        f"std::move(op.outputs_[{i}])"
                        for i in range(len(f.func.returns))
                    )
                    ret_expr = f"std::make_tuple({moved})"
            elif k is SchemaKind.inplace:
                ret_expr = "self"
            elif k is SchemaKind.out:
                if len(f.func.returns) == 1:
                    ret_expr = f.func.arguments.out[0].name
                else:
                    refs = ", ".join(a.name for a in f.func.arguments.out)
                    ret_expr = f"std::forward_as_tuple({refs})"
            sig_body.append(f"return {ret_expr};")  # type: ignore[possibly-undefined]  # TODO: audit

            sig_body_str = "\n".join(sig_body)

            # For an overview of what this template code looks like, see
            # https://github.com/pytorch/rfcs/pull/9
            return f"""\
{
                self.gen_class(
                    f,
                    k,
                    class_name=class_name,
                    parent_class=parent_class,
                    generate_super=self.g.out.structured_inherits is not None,
                )
            }

{sig.defn()} {{
{sig_body_str}
}}
"""

        elif self.target is Target.REGISTRATION:
            return f'm.impl("{f.func.name}", TORCH_FN({sig.name()}));'
        else:
            assert_never(self.target)
            # Silence mypy's "Missing return statement" error
            return None
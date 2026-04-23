def _exec_in_closure(self, source, globals, locals):
        """ Run source code in closure so code object created within source
            can find variables in locals correctly

            returns True if the source is executed, False otherwise
        """

        # Determine if the source should be executed in closure. Only when the
        # source compiled to multiple code objects, we should use this feature.
        # Otherwise, we can just raise an exception and normal exec will be used.

        code = compile(source, "<string>", "exec")
        if not any(isinstance(const, CodeType) for const in code.co_consts):
            return False

        # locals could be a proxy which does not support pop
        # copy it first to avoid modifying the original locals
        locals_copy = dict(locals)

        locals_copy["__pdb_eval__"] = {
            "result": None,
            "write_back": {}
        }

        # If the source is an expression, we need to print its value
        try:
            compile(source, "<string>", "eval")
        except SyntaxError:
            pass
        else:
            source = "__pdb_eval__['result'] = " + source

        # Add write-back to update the locals
        source = ("try:\n" +
                  textwrap.indent(source, "  ") + "\n" +
                  "finally:\n" +
                  "  __pdb_eval__['write_back'] = locals()")

        # Build a closure source code with freevars from locals like:
        # def __pdb_outer():
        #   var = None
        #   def __pdb_scope():  # This is the code object we want to execute
        #     nonlocal var
        #     <source>
        #   return __pdb_scope.__code__
        source_with_closure = ("def __pdb_outer():\n" +
                               "\n".join(f"  {var} = None" for var in locals_copy) + "\n" +
                               "  def __pdb_scope():\n" +
                               "\n".join(f"    nonlocal {var}" for var in locals_copy) + "\n" +
                               textwrap.indent(source, "    ") + "\n" +
                               "  return __pdb_scope.__code__"
                               )

        # Get the code object of __pdb_scope()
        # The exec fills locals_copy with the __pdb_outer() function and we can call
        # that to get the code object of __pdb_scope()
        ns = {}
        try:
            exec(source_with_closure, {}, ns)
        except Exception:
            return False
        code = ns["__pdb_outer"]()

        cells = tuple(types.CellType(locals_copy.get(var)) for var in code.co_freevars)

        try:
            exec(code, globals, locals_copy, closure=cells)
        except Exception:
            return False

        # get the data we need from the statement
        pdb_eval = locals_copy["__pdb_eval__"]

        # __pdb_eval__ should not be updated back to locals
        pdb_eval["write_back"].pop("__pdb_eval__")

        # Write all local variables back to locals
        locals.update(pdb_eval["write_back"])
        eval_result = pdb_eval["result"]
        if eval_result is not None:
            self.message(repr(eval_result))

        return True
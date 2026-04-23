def process_ir_type(
    typ: Type, properties: LazyIrProperties, *, symint: bool
) -> BaseCType | VectorCType | OptionalCType | ListCType:
    """
    This function takes a type from NativeFunctions and converts it for use with
    lazy tensor codegen.

    Type conversion for lazy currently consists of
     (1) changing at::Tensors into lazy::Values
     (2) wrapping everything in a BaseCType
     (3) making cpp-reference types into cpp-value types (e.g. vector instead of IntArrayRef)

    (1) converts at::Tensors to lazy::Values (which wrap lazy::Nodes, with which Lazy IR represents tensors.)
    There is special handling for Optional[Tensor] or list[Tensor], etc- hence 'tensor-like'

    This is incomplete- there are assertions in places that it's expected to need to add
    more types as the codegen is used with more operators.
    """
    if isinstance(typ, BaseType):
        if typ.name == BaseTy.Tensor:
            return BaseCType(getValueT())
        elif typ.name == BaseTy.Scalar:
            if properties.TreatScalarsAsConstants:
                return BaseCType(scalarT)
            # at::scalar has special handling,
            # and is wrapped in an lazy::Value just like at::tensor
            return BaseCType(getValueT())
        elif typ.name == BaseTy.ScalarType:
            return BaseCType(scalarTypeT)
        elif typ.name == BaseTy.int:
            return BaseCType(longT)
        elif typ.name == BaseTy.SymInt:
            if symint:
                return BaseCType(getValueT())
            else:
                return BaseCType(longT)
        elif typ.name == BaseTy.bool:
            return BaseCType(boolT)
        elif typ.name == BaseTy.float:
            return BaseCType(doubleT)
        elif typ.name == BaseTy.str:
            return BaseCType(stringT)
        elif typ.name == BaseTy.Device:
            return BaseCType(deviceT)
        elif typ.name == BaseTy.Generator:
            return BaseCType(generatorT)
        elif typ.name == BaseTy.Layout:
            return BaseCType(layoutT)
        elif typ.name == BaseTy.MemoryFormat:
            return BaseCType(memoryFormatT)
        else:
            raise AssertionError(f"TODO add support for type {repr(typ)}")
    elif isinstance(typ, OptionalType):
        return OptionalCType(process_ir_type(typ.elem, properties, symint=symint))
    elif isinstance(typ, ListType):
        if str(typ.elem) == "Tensor?":
            # TODO(whc) is this actually correct? or should it use a Vector like above
            return ListCType(OptionalCType(BaseCType(getValueT())))
        elif str(typ.elem) == "Tensor":
            # this is a TensorList which comes in from GetTensorList as a Value
            return BaseCType(tensorListValueT)
        elif typ.elem == BaseType(BaseTy.SymInt):
            # TODO: return a value type.  The problem here is analogous to
            # the problem with tensorListValueT: if you have SymInt[] you
            # cannot conveniently save the list of Value directly, as nodes
            # expect to save values as a vector for ALL arguments.  So you
            # need a separate IR node that represents all of the size nodes
            # assembled into a list.  I'm not an LTC dev so I don't want to
            # figure it out right now.  Y'all figure it out...
            return VectorCType(BaseCType(longT))

        else:
            return VectorCType(process_ir_type(typ.elem, properties, symint=symint))
    else:
        raise AssertionError(f"unrecognized type {repr(typ)}")
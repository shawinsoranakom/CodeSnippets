def forwardref_method(input: "ForwardRefModel") -> "ForwardRefModel":
    return ForwardRefModel(x=input.x + 1)
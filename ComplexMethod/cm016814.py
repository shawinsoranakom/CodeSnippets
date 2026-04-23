def VALIDATE_INPUTS(cls, input_types, input1=None, input2=None):
        if input1 is not None:
            if not isinstance(input1, (torch.Tensor, float)):
                return f"Invalid type of input1: {type(input1)}"
        if input2 is not None:
            if not isinstance(input2, (torch.Tensor, float)):
                return f"Invalid type of input2: {type(input2)}"

        if 'input1' in input_types:
            if input_types['input1'] not in ["IMAGE", "FLOAT"]:
                return f"Invalid type of input1: {input_types['input1']}"
        if 'input2' in input_types:
            if input_types['input2'] not in ["IMAGE", "FLOAT"]:
                return f"Invalid type of input2: {input_types['input2']}"

        return True
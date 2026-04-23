def get_scan_combine_fn(name, associative=True, parameters=None):
    def add(x: torch.Tensor, y: torch.Tensor):
        return x + y

    def adds(x: torch.Tensor, y: torch.Tensor):
        return x + x, y + y

    def mul(x: torch.Tensor, y: torch.Tensor):
        return x * y

    def div(x: torch.Tensor, y: torch.Tensor):
        return x / y

    def s5_operator(x: torch.Tensor, y: torch.Tensor):
        A_i, Bu_i = x
        A_j, Bu_j = y
        return A_j * A_i, A_j * Bu_i + Bu_j

    def different_input_size_operator(x: torch.Tensor, y: torch.Tensor):
        x_o, dA_o, dB_o, C_o, y_o = x
        x_n, dA_n, dB_n, C_n, y_n = y

        x_new = x_n + x_o
        y_new = torch.einsum("bdn,bn->bd", x_new, C_n)

        return x_new, dA_n + 0.0, dB_n + 0.0, C_n + 0.0, y_new

    def tuple_fct(x, y):
        return (x[0] + y[0], x[1] * y[1])

    def complex_pointwise(x, y):
        return {
            "i": x["i"] * y["i"],
            "j": (
                [x["j"][0][0] * y["j"][0][0]],
                [{"o": x["j"][1][0]["o"] + y["j"][1][0]["o"]}],
            ),
        }

    def non_pointwise(x: torch.Tensor, y: torch.Tensor):
        W = torch.arange(4, dtype=torch.float, device=x.device).view(2, 2)
        return x @ W + y @ W

    def RNN(x: torch.Tensor, y: torch.Tensor):
        c_new = y @ parameters[0] + parameters[1]
        h_new = torch.tanh(c_new + x @ parameters[2] + parameters[3])
        return h_new, h_new.clone()

    def fct_c1_no_grad(x: torch.Tensor, y: torch.Tensor):
        h_new = torch.tanh(x[0] + x[1] + y)
        c2 = x[1] + y
        with torch.no_grad():
            c1 = x[0] + y
        return (c1, c2), h_new

    if name == "add":
        fct = add
    elif name == "adds":
        fct = adds
    elif name == "mul":
        fct = mul
    elif name == "div":
        fct = div
    elif name == "s5_operator":
        fct = s5_operator
    elif name == "different_input_size_operator":
        fct = different_input_size_operator
    elif name == "tuple_fct":
        fct = tuple_fct
    elif name == "complex_pointwise":
        fct = complex_pointwise
    elif name == "non_pointwise":
        fct = non_pointwise
    elif name == "RNN":
        fct = RNN
    elif name == "fct_c1_no_grad":
        fct = fct_c1_no_grad
    else:
        raise ValueError("Combine_fn name unknown!")

    if not associative:
        return lambda x, y: (fct(x, y), fct(x, y))
    else:
        return fct
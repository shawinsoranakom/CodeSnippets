def __init__(self, args, kwargs):
        self.arg_types = ['t' if self._is_tensor_input(arg) else 's' for arg in args]
        self.kwarg_types = {k: 't' if self._is_tensor_input(v) else 's' for k, v in kwargs.items()}
        self.tensor_args = [arg for arg in args if self._is_tensor_input(arg)]
        self.nontensor_args = [arg for arg in args if not self._is_tensor_input(arg)]
        self.tensor_kwargs = {k: v for k, v in kwargs.items() if self._is_tensor_input(v)}
        self.nontensor_kwargs = {k: v for k, v in kwargs.items() if not self._is_tensor_input(v)}
        self.all_tensors = [*self.tensor_args, *[v for k, v in self.tensor_kwargs.items()]]
        self.kwarg_order = [k for k, v in kwargs.items()]
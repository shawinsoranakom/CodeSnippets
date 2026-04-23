def to_folder(
        self, folder: str | os.PathLike[str], module_name: str = "FxModule"
    ) -> None:
        """Dumps out module to ``folder`` with ``module_name`` so that it can be
        imported with ``from <folder> import <module_name>``

        Args:

            folder (Union[str, os.PathLike]): The folder to write the code out to

            module_name (str): Top-level name to use for the ``Module`` while
                writing out the code
        """
        folder = Path(folder)
        Path(folder).mkdir(exist_ok=True)
        torch.save(self.state_dict(), folder / "state_dict.pt")
        tab = " " * 4
        custom_builtins = "\n".join([v.import_str for v in _custom_builtins.values()])
        model_str = f"""
import torch
{custom_builtins}

from torch.nn import *
class {module_name}(torch.nn.Module):
    def __init__(self):
        super().__init__()
"""

        def _gen_model_repr(module_name: str, module: torch.nn.Module) -> str | None:
            safe_reprs = [
                nn.Linear,
                nn.Conv1d,
                nn.Conv2d,
                nn.Conv3d,
                nn.BatchNorm1d,
                nn.BatchNorm2d,
                nn.BatchNorm3d,
            ]
            if type(module) in safe_reprs:
                return f"{module.__repr__()}"
            else:
                return None

        blobified_modules: list[str] = []
        for module_name, module in self.named_children():
            module_str = _gen_model_repr(module_name, module)
            if module_str is None:
                module_file = folder / f"{module_name}.pt"
                torch.save(module, module_file)
                blobified_modules.append(module_name)
                module_repr = module.__repr__().replace("\r", " ").replace("\n", " ")
                # weights_only=False as this is legacy code that saves the model
                module_load_str = f"torch.load(r'{module_file}', weights_only=False)"
                model_str += f"{tab * 2}setattr(self, '{module_name}', {module_load_str}) # {module_repr}\n"
            else:
                model_str += f"{tab * 2}setattr(self, '{module_name}', {module_str})\n"

        for buffer_name, buffer in self._buffers.items():
            if buffer is None:
                continue
            model_str += f"{tab * 2}self.register_buffer('{buffer_name}', torch.empty({list(buffer.shape)}, dtype={buffer.dtype}))\n"

        for param_name, param in self._parameters.items():
            if param is None:
                continue
            model_str += f"{tab * 2}setattr(self, '{param_name}', torch.nn.Parameter(torch.empty({list(param.shape)}, dtype={param.dtype})))\n"

        model_str += (
            f"{tab * 2}self.load_state_dict(torch.load(r'{folder}/state_dict.pt'))\n"
        )
        model_str += f"{_addindent(self.code, 4)}\n"

        module_file = folder / "module.py"
        module_file.write_text(model_str)

        init_file = folder / "__init__.py"
        init_file.write_text("from .module import *")

        if len(blobified_modules) > 0:
            warnings.warn(
                "Was not able to save the following children modules as reprs -"
                f"saved as pickled files instead: {blobified_modules}"
            )
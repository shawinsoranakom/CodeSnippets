def helper(operator):
            t_mps = torch.tensor([1, 2, 3, 4], device="mps")
            t_cpu = torch.tensor([1, 2, 3, 4], device="cpu")

            # contiguous view
            x_mps = t_mps[2:]  # 3, 4
            y_mps = t_mps[:2]  # 1, 2

            x_cpu = t_cpu[2:]
            y_cpu = t_cpu[:2]

            res_mps = res_cpu = None
            if operator == "<=":
                res_mps = x_mps <= y_mps
                res_cpu = x_cpu <= y_cpu
            elif operator == "<":
                res_mps = x_mps < y_mps
                res_cpu = x_cpu < y_cpu
            elif operator == ">=":
                res_mps = x_mps >= y_mps
                res_cpu = x_cpu >= y_cpu
            elif operator == ">":
                res_mps = x_mps >= y_mps
                res_cpu = x_cpu >= y_cpu
            elif operator == "==":
                res_mps = x_mps == y_mps
                res_cpu = x_cpu == y_cpu
            elif operator == "!=":
                res_mps = x_mps != y_mps
                res_cpu = x_cpu != y_cpu
            elif operator == "stack":
                res_mps = torch.stack((y_mps, x_mps), dim=-1)
                res_cpu = torch.stack((y_cpu, x_cpu), dim=-1)

            self.assertEqual(res_mps, res_cpu)
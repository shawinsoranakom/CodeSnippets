def foo():
            y = torch.tensor(0)
            z = 0
            while int(y.add_(1)) < 20:
                if int(y) < 10:
                    for i in range(6):
                        if i == 3:
                            continue
                        else:
                            if i > 3:
                                break
                        z += 2
                if int(y) == 18:
                    break
                if int(y) == 15:
                    continue
                z += 1
            return int(y), z
def one_to_one_match(row, col):
            cont = 0
            for j in range(len(recallMat[0])):
                if (
                    recallMat[row, j] >= self.area_recall_constraint
                    and precisionMat[row, j] >= self.area_precision_constraint
                ):
                    cont = cont + 1
            if cont != 1:
                return False
            cont = 0
            for i in range(len(recallMat)):
                if (
                    recallMat[i, col] >= self.area_recall_constraint
                    and precisionMat[i, col] >= self.area_precision_constraint
                ):
                    cont = cont + 1
            if cont != 1:
                return False

            if (
                recallMat[row, col] >= self.area_recall_constraint
                and precisionMat[row, col] >= self.area_precision_constraint
            ):
                return True
            return False
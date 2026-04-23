def concat(seq1, seq2):
            if seq1 and seq2:
                f1, f2 = seq1[-1], seq2[0]
                if (
                    f1.type == 'many2one' and f2.type == 'one2many'
                    and f1.name == f2.inverse_name
                    and f1.model_name == f2.comodel_name
                    and f1.comodel_name == f2.model_name
                ):
                    return concat(seq1[:-1], seq2[1:])
            return seq1 + seq2
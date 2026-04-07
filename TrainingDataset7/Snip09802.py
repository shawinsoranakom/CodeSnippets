def callproc(self, name, args=None):
            if not isinstance(name, sql.Identifier):
                name = sql.Identifier(name)

            qparts = [sql.SQL("SELECT * FROM "), name, sql.SQL("(")]
            if args:
                for item in args:
                    qparts.append(sql.Literal(item))
                    qparts.append(sql.SQL(","))
                del qparts[-1]

            qparts.append(sql.SQL(")"))
            stmt = sql.Composed(qparts)
            self.execute(stmt)
            return args
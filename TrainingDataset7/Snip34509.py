def test_precedence(self):
        # (False and False) or True == True   <- we want this one, like Python
        # False and (False or True) == False
        self.assertCalcEqual(True, [False, "and", False, "or", True])

        # True or (False and False) == True   <- we want this one, like Python
        # (True or False) and False == False
        self.assertCalcEqual(True, [True, "or", False, "and", False])

        # (1 or 1) == 2  -> False
        # 1 or (1 == 2)  -> True   <- we want this one
        self.assertCalcEqual(True, [1, "or", 1, "==", 2])

        self.assertCalcEqual(True, [True, "==", True, "or", True, "==", False])

        self.assertEqual(
            "(or (and (== (literal 1) (literal 2)) (literal 3)) (literal 4))",
            repr(IfParser([1, "==", 2, "and", 3, "or", 4]).parse()),
        )
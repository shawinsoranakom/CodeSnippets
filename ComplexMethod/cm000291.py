def train(self, x, y):
        """
        train:
        @param x: a one-dimensional numpy array
        @param y: a one-dimensional numpy array.
        The contents of y are the labels for the corresponding X values

        train() does not have a return value

        Examples:
        1. Try to train when x & y are of same length & 1 dimensions (No errors)
        >>> dt = DecisionTree()
        >>> dt.train(np.array([10,20,30,40,50]),np.array([0,0,0,1,1]))

        2. Try to train when x is 2 dimensions
        >>> dt = DecisionTree()
        >>> dt.train(np.array([[1,2,3,4,5],[1,2,3,4,5]]),np.array([0,0,0,1,1]))
        Traceback (most recent call last):
            ...
        ValueError: Input data set must be one-dimensional

        3. Try to train when x and y are not of the same length
        >>> dt = DecisionTree()
        >>> dt.train(np.array([1,2,3,4,5]),np.array([[0,0,0,1,1],[0,0,0,1,1]]))
        Traceback (most recent call last):
            ...
        ValueError: x and y have different lengths

        4. Try to train when x & y are of the same length but different dimensions
        >>> dt = DecisionTree()
        >>> dt.train(np.array([1,2,3,4,5]),np.array([[1],[2],[3],[4],[5]]))
        Traceback (most recent call last):
            ...
        ValueError: Data set labels must be one-dimensional

        This section is to check that the inputs conform to our dimensionality
        constraints
        """
        if x.ndim != 1:
            raise ValueError("Input data set must be one-dimensional")
        if len(x) != len(y):
            raise ValueError("x and y have different lengths")
        if y.ndim != 1:
            raise ValueError("Data set labels must be one-dimensional")

        if len(x) < 2 * self.min_leaf_size:
            self.prediction = np.mean(y)
            return

        if self.depth == 1:
            self.prediction = np.mean(y)
            return

        best_split = 0
        min_error = self.mean_squared_error(x, np.mean(y)) * 2

        """
        loop over all possible splits for the decision tree. find the best split.
        if no split exists that is less than 2 * error for the entire array
        then the data set is not split and the average for the entire array is used as
        the predictor
        """
        for i in range(len(x)):
            if len(x[:i]) < self.min_leaf_size:  # noqa: SIM114
                continue
            elif len(x[i:]) < self.min_leaf_size:
                continue
            else:
                error_left = self.mean_squared_error(x[:i], np.mean(y[:i]))
                error_right = self.mean_squared_error(x[i:], np.mean(y[i:]))
                error = error_left + error_right
                if error < min_error:
                    best_split = i
                    min_error = error

        if best_split != 0:
            left_x = x[:best_split]
            left_y = y[:best_split]
            right_x = x[best_split:]
            right_y = y[best_split:]

            self.decision_boundary = x[best_split]
            self.left = DecisionTree(
                depth=self.depth - 1, min_leaf_size=self.min_leaf_size
            )
            self.right = DecisionTree(
                depth=self.depth - 1, min_leaf_size=self.min_leaf_size
            )
            self.left.train(left_x, left_y)
            self.right.train(right_x, right_y)
        else:
            self.prediction = np.mean(y)

        return
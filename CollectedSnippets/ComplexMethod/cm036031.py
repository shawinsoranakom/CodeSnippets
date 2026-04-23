def walk_tree(self, h: History, i: Player, pi_i: float, pi_neg_i: float) -> float:
        """
        ### Walk Tree

        This function walks the game tree.

        * `h` is the current history $h$
        * `i` is the player $i$ that we are computing regrets of
        * [`pi_i`](#HistoryProbability) is
         $\pi^{\sigma^t}_i(h)$
        * [`pi_neg_i`](#HistoryProbability) is
         $\pi^{\sigma^t}_{-i}(h)$

        It returns the expected utility, for the history $h$
        $$\sum_{z \in Z_h} \pi^\sigma(h, z) u_i(z)$$
        where $Z_h$ is the set of terminal histories with prefix $h$

        While walking the tee it updates the total regrets $\textcolor{orange}{R^T_i(I, a)}$.
        """

        # If it's a terminal history $h \in Z$ return the terminal utility $u_i(h)$.
        if h.is_terminal():
            return h.terminal_utility(i)
        # If it's a chance event $P(h) = c$ sample a and go to next step.
        elif h.is_chance():
            a = h.sample_chance()
            return self.walk_tree(h + a, i, pi_i, pi_neg_i)

        # Get current player's information set for $h$
        I = self._get_info_set(h)
        # To store $\sum_{z \in Z_h} \pi^\sigma(h, z) u_i(z)$
        v = 0
        # To store
        # $$\sum_{z \in Z_h} \pi^{\sigma^t |_{I \rightarrow a}}(h, z) u_i(z)$$
        # for each action $a \in A(h)$
        va = {}

        # Iterate through all actions
        for a in I.actions():
            # If the current player is $i$,
            if i == h.player():
                # \begin{align}
                # \pi^{\sigma^t}_i(h + a) &= \pi^{\sigma^t}_i(h) \sigma^t_i(I)(a) \\
                # \pi^{\sigma^t}_{-i}(h + a) &= \pi^{\sigma^t}_{-i}(h)
                # \end{align}
                va[a] = self.walk_tree(h + a, i, pi_i * I.strategy[a], pi_neg_i)
            # Otherwise,
            else:
                # \begin{align}
                # \pi^{\sigma^t}_i(h + a) &= \pi^{\sigma^t}_i(h)  \\
                # \pi^{\sigma^t}_{-i}(h + a) &= \pi^{\sigma^t}_{-i}(h) * \sigma^t_i(I)(a)
                # \end{align}
                va[a] = self.walk_tree(h + a, i, pi_i, pi_neg_i * I.strategy[a])
            # $$\sum_{z \in Z_h} \pi^\sigma(h, z) u_i(z) =
            # \sum_{a \in A(I)} \Bigg[ \sigma^t_i(I)(a)
            # \sum_{z \in Z_h} \pi^{\sigma^t |_{I \rightarrow a}}(h, z) u_i(z)
            # \Bigg]$$
            v = v + I.strategy[a] * va[a]

        # If the current player is $i$,
        # update the cumulative strategies and total regrets
        if h.player() == i:
            # Update cumulative strategies
            # $$\sum_{t=1}^T \pi_i^{\sigma^t}(I)\textcolor{lightgreen}{\sigma^t(I)(a)}
            # = \sum_{t=1}^T \Big[ \sum_{h \in I} \pi_i^{\sigma^t}(h)
            # \textcolor{lightgreen}{\sigma^t(I)(a)} \Big]$$
            for a in I.actions():
                I.cumulative_strategy[a] = I.cumulative_strategy[a] + pi_i * I.strategy[a]
            # \begin{align}
            # \textcolor{coral}{\tilde{r}^t_i(I, a)} &=
            #  \textcolor{pink}{\tilde{v}_i(\sigma^t |_{I \rightarrow a}, I)} -
            #  \textcolor{pink}{\tilde{v}_i(\sigma^t, I)} \\
            #  &=
            #  \pi^{\sigma^t}_{-i} (h) \Big(
            #  \sum_{z \in Z_h} \pi^{\sigma^t |_{I \rightarrow a}}(h, z) u_i(z) -
            #  \sum_{z \in Z_h} \pi^\sigma(h, z) u_i(z)
            #  \Big) \\
            # T \textcolor{orange}{R^T_i(I, a)} &=
            #  \sum_{t=1}^T \textcolor{coral}{\tilde{r}^t_i(I, a)}
            # \end{align}
            for a in I.actions():
                I.regret[a] += pi_neg_i * (va[a] - v)

            # Update the strategy $\textcolor{lightgreen}{\sigma^t(I)(a)}$
            I.calculate_strategy()

        # Return the expected utility for player $i$,
        # $$\sum_{z \in Z_h} \pi^\sigma(h, z) u_i(z)$$
        return v
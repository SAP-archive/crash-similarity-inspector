class DP:
    """
    Several dynamic programming algorithms that will be used.
    """
    @staticmethod
    def lcs_position(seq1, seq2):
        """
        Obtain the position information of longest common subsequence.
        Args:
            seq1: A sequence to be iterated.
            seq2: A sequence to be iterated.
        Returns:
            The position information of longest common subsequence.
        """
        m, n = len(seq1), len(seq2)
        # initialize
        dp = [[[] for _ in range(n + 1)] for _ in range(m + 1)]
        # fill
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + [(i - 1, j - 1)]
                else:
                    # column preference
                    dp[i][j] = max(dp[i][j-1], dp[i-1][j], key=len)
        return dp[-1][-1]

    @staticmethod
    def normalized_dist(seq1, seq2):
        """
        Obtain the normalized distance between two sequences.
        Args:
            seq1: A sequence to be iterated.
            seq2: A sequence to be iterated.
        Returns:
            The normalized distance between two sequences.
        """
        m, n = len(seq1), len(seq2)
        # initialize
        dp = [[i + j for j in range(n + 1)] for i in range(m + 1)]
        # fill
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                dist = 1 if seq1[i-1] != seq2[j-1] else 0
                dp[i][j] = min(dp[i-1][j-1] + dist,
                               min(dp[i-1][j], dp[i][j-1]) + 1)
        return dp[-1][-1] / max(m, n)


class UF:
    """
    An implementation of Union-Find algorithm.
    Attributes:
        id: The identifier of each tree.
        rank: The weight of each tree.
    """
    def __init__(self, n):
        self.id = list(range(n))
        self.rank = [0] * n

    def find(self, node):
        """
        Obtain the tree identifier for an element node via path compression.
        Args:
            node: An element node.
        Returns:
            The tree identifier.
        """
        while node != self.id[node]:
            # path compression by halving
            self.id[node] = self.id[self.id[node]]
            node = self.id[node]
        return node

    def union(self, u, v):
        """
        Combine trees containing two elements into a single tree by rank.
        Args:
            u: An element node.
            v: An element node.
        """
        l, r = self.find(u), self.find(v)
        if l == r:
            return
        # attach smaller tree to larger tree
        if self.rank[l] < self.rank[r]:
            self.id[l] = r
        elif self.rank[r] < self.rank[l]:
            self.id[r] = l
        else:
            self.id[l] = r
            self.rank[r] += 1

class DP:
    """
    Several dynamic programming algorithms that will be used.
    """
    @staticmethod
    def lcs_position(seq1, seq2):
        """
        Obtain the position information of longest common subsequence via top first.
        Args:
            seq1: A sequence to be iterated.
            seq2: A sequence to be iterated.
        Returns:
            The position information of longest common subsequence.
        """
        pos1, pos2 = [], []
        m, n = len(seq1), len(seq2)
        # initialize dp matrix with 0
        dp = [[0 for _ in range(n + 1)] for _ in range(m + 1)]
        # fill dp matrix
        for i in range(m + 1):
            for j in range(n + 1):
                if i == 0 or j == 0:
                    dp[i][j] = 0
                elif seq1[m-i] == seq2[n-j]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        # obtain positions of longest common subsequence
        i, j = m, n
        while i > 0 and j > 0:
            if seq1[m-i] == seq2[n-j]:
                pos1.append(m - i)
                pos2.append(n - j)
                i -= 1
                j -= 1
            elif dp[i - 1][j] > dp[i][j - 1]:
                i -= 1
            else:
                j -= 1
        return pos1, pos2

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
        # initialize dp matrix
        dp = [[i + j for j in range(n + 1)] for i in range(m + 1)]
        # fill dp matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dist = 0
                else:
                    dist = 1
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + dist)
        return dp[m][n] / max(m, n)


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
            node = self.id[node] = self.id[self.id[node]]
        return node

    def union(self, p, q):
        """
        Combine trees containing two element nodes into a single tree.
        Args:
            p: An element node.
            q: An element node.
        """
        i, j = self.find(p), self.find(q)
        if i == j:
            return None
        if self.rank[i] < self.rank[j]:
            self.id[i] = j
        else:
            if self.rank[i] == self.rank[j]:
                self.rank[i] += 1
            self.id[j] = i

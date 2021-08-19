import configparser
import math
import os

from log import Log
from utils import DP


class Calculate:
    """
    Calculate crash dump similarity through the mathematical model.
    Attributes:
        order_pair: The component order information within crash dump pair.
        block_pair: The function block information within crash dump pair.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(os.getcwd(), "config.ini")
    config.read(config_path)
    # Model
    m = config.getfloat("model", "m")
    n = config.getfloat("model", "n")

    def __init__(self, order_pair, block_pair):
        self.order_pair = order_pair
        self.block_pair = block_pair

    def obtain_feature(self):
        """
        Obtain the features used for calculation through dump pair information.
        Returns:
            The features used for calculation.
        """
        positions, distances = [], []
        for i, j in DP().lcs_position(self.order_pair[0], self.order_pair[1]):
            positions.append(max(i, j))
            distances.append(DP().normalized_dist(self.block_pair[0][i], self.block_pair[1][j]))
        return list(zip(positions, distances))

    def calculate_sim(self, m=m, n=n, debug=False):
        """
        Calculate the crash dump similarity under current parameters.
        Args:
            m: The parameter for component position.
            n: The parameter for component distance.
            debug: Whether to print the calculation formula.
        Returns:
            sim: The similarity result.
        """
        numerator = denominator = 0.0
        features = self.obtain_feature()
        for pos, dist in features:
            numerator += math.exp(-m * pos) * math.exp(-n * dist)
        max_len = len(max(self.order_pair, key=len))
        for i in range(max_len):
            denominator += math.exp(-m * i)
        sim = numerator / denominator
        return sim if not debug else Log().formula_print(features, max_len, sim)

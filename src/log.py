import configparser
import os
import textwrap


class Log:
    """
    Print a few messages for the specific feature.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(os.getcwd(), "config.ini")
    config.read(config_path)
    # Model
    m = config.getfloat("model", "m")
    n = config.getfloat("model", "n")
    # Log
    width = config.getint("log", "width")

    def dump_print(self, message):
        """
        Print a pair of crash dumps in comparison way.
        Args:
            message: Crash dump message to be printed.
        """
        print("\n", end="")
        # print the left part
        cursor_up = 0
        for i in range(len(message[0])):
            blocks = textwrap.fill(" ".join(message[1][i]), width=self.width)
            cursor_up += len(blocks.split("\n")) + 1
            print(f"\x1b[0;36m{message[0][i]}\x1b[0m")
            print(blocks)
        print(f"\x1b[{cursor_up}A", end="")
        # print the right part
        cursor_down = 0
        for i in range(len(message[2])):
            blocks = textwrap.fill(" ".join(message[3][i]), width=self.width)
            cursor_down += len(blocks.split("\n")) + 1
            print(f"\x1b[{self.width}C  |  \x1b[0;36m{message[2][i]}\x1b[0m")
            for line in blocks.split("\n"):
                print(f"\x1b[{self.width}C  |  {line}")
        if cursor_down < cursor_up:
            for _ in range(cursor_up - cursor_down):
                print(f"\x1b[{self.width}C  |")
        print("\n", end="")

    def formula_print(self, features, len_max, sim):
        """
        Print the formula of similarity calculation.
        Args:
            features: Feature values of position and distance.
            len_max: The longer length of 2 component sequences.
            sim: The similarity result.
        """
        if features:
            numerator = " + ".join(f"e^-{self.m}*{pos}*e^-{self.n}*{dist:.4f}" for pos, dist in features)
            denominator = " + ".join(f"e^-{self.m}*{i}" for i in range(len_max))
            print(f"             {numerator}")
            print(f"Similarity = {'-' * max(len(numerator), len(denominator))} = {sim:.2%}")
            print(f"             {denominator}")
        else:
            print("Similarity = 0.00%")
        print("\n", end="")

    def chart_print(self, message):
        """
        Output stop words statistics via bar chart.
        Args:
            message: Stop words message to be printed.
        """
        print("\n", end="")
        tick = "▇"
        slim_tick = "▏"
        max_len = message[0][1]
        for msg in message:
            num = int(msg[1] / max_len * self.width)
            if num >= 1:
                print(f"{tick * num} {msg[0]}:{msg[1]}")
            else:
                print(f"{slim_tick} {msg[0]}:{msg[1]}")
        print("\n", end="")

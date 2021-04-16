import configparser
import os
import re
import subprocess

from component import Component


class Knowledge:
    """
    Add component knowledge and obtain cpnt_order, func_block for calculation.
    Attributes:
        processed: Processed crash dump composed of function and path.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(os.getcwd(), "config.ini")
    config.read(config_path)
    # MongoDB
    host = config.get("mongodb", "host")
    port = config.getint("mongodb", "port")
    # Stop
    stop_words = config.get("stop", "words")

    def __init__(self, processed):
        self.processed = processed

    @staticmethod
    def unboxing(function):
        """
        Extract the required part of function and divide it into blocks.
        Args:
            function: A original function name.
        Returns:
            Function blocks are composed of class, namespace, ...
        """
        blocks = []
        # handle anonymous namespace
        if "(anonymous namespace)" in function:
            function = function.replace("(anonymous namespace)", "")
        if "(" in function:
            function = function[:function.find("(")]
        if "<" in function:
            function = function[:function.find("<")]
        # remove return type
        if " " in function:
            function = function[function.rfind(" ") + 1:]
        # filter function with special characters
        if re.search(r"[^\w:~]", function):
            return blocks
        for block in [i for i in function.split("::") if i]:
            blocks.append(block)
        return blocks

    @staticmethod
    def execute_shell(command):
        """
        Execute a specified shell command.
        Args:
            command: The input command.
        Returns:
            The output after command execution.
        """
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, _ = pipe.communicate()
        return stdout.decode("utf-8")[:-1]

    def to_component(self, path):
        """
        Convert the absolute path to possible component name.
        Args:
            path: An absolute path or base name.
        Returns:
            The component which current stack frame belongs to.
        """
        git_root = "hana"
        if "/" not in path:
            cmd = "find {} -name {}".format(git_root, path)
            full_path = self.execute_shell(cmd.split(" "))
        else:
            full_path = "{}/{}".format(git_root, path)
        if not full_path or "\n" in full_path:
            component = "UNKNOWN"
        else:
            component = Component().best_matched(full_path)
        return component

    def add_knowledge(self):
        """
        Add component knowledge and obtain cpnt_order, func_block for calculation.
        Returns:
            The cpnt_order and func_block for calculation.
        """
        cpnt_order, func_block = [], []
        for frame in self.processed:
            function, path = frame
            # filter stop words
            base_name = path[path.rindex("/") + 1:] if "/" in path else path
            if base_name in self.stop_words:
                continue
            # demangling
            if function.startswith("_Z"):
                cmd = "c++filt -p {}".format(function)
                function = self.execute_shell(cmd.split(" "))
            function = self.unboxing(function)
            if not function:
                continue
            component = self.to_component(path)
            # obtain cpnt_order and func_block
            if not cpnt_order or component != cpnt_order[-1]:
                cpnt_order.append(component)
                func_block.append(function)
            else:
                func_block[-1].extend(function)
        return cpnt_order, func_block

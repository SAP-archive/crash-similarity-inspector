import re


class Process:
    """
    Data preprocessing for crash dump string.
    Attributes:
        dump: A crash dump string.
    """
    def __init__(self, dump):
        self.dump = dump

    def pre_process(self):
        """
        Extract the backtrace part of the original crash dump string.
        Returns:
            processed: Processed string with function, path information.
        """
        processed = []
        # call stack pattern
        stack_pattern = re.compile(r"\n(\[CRASH_STACK][\s\S]+)\[CRASH_REGISTERS]", re.M)
        content = stack_pattern.findall(self.dump)
        stack = content[0]
        # backtrace pattern
        pattern = re.compile(r"-\n[ ]*\d+:[ ](.+)[^-]+Source:[ ](.+):", re.M)
        frames = pattern.findall(stack)
        for frame in frames:
            function, path = frame
            # remove offset
            offset_pattern = re.compile(r"([ ]const)*[ ][+][ ]0x\w+")
            function = re.sub(offset_pattern, "", function)
            processed.append([function, path])
        return processed

    def internal_process(self):
        """
        Extract the backtrace part of the internal crash dump string.
        Returns:
            processed: Processed string with function, path information.
        """
        processed = []
        backtrace = self.dump[:self.dump.find("\n\n")]
        pattern = re.compile(r"^\d+:[ ](.+)[ ]at[ ](.+)", re.M)
        frames = pattern.findall(backtrace)
        for frame in frames:
            function, path = frame
            processed.append([function, path])
        return processed

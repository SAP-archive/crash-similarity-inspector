import re

from collections import Counter
from etl import ETL
from log import Log
from process import Process


class StopWord:
    """
    Count file names that can be filtered.
    """
    @staticmethod
    def obtain_word(roots, processed):
        """
        Obtain stop words from crash dump's backtrace.
        Args:
            roots: Possible root causes in exception.
            processed: Processed string with function, path information.
        Returns:
            The stop words.
        """
        words = []
        functions, paths = [i[0] for i in processed], [i[1] for i in processed]
        for root in roots:
            if root not in functions:
                continue
            for path in paths[:functions.index(root)]:
                file_name = path[path.rindex("/") + 1:] if "/" in path else path
                words.append(file_name)
            break
        return words

    def count_word(self):
        """
        Count stop words and output statistics.
        """
        word_list = []
        count = 0
        result = ETL().extract_word()
        for row in result:
            count += 1
            test_id = row[0]
            print("{}, {}/{}".format(test_id, count, len(result)))
            try:
                dump = ETL().extract_cdb(test_id)
            except (IndexError, UnicodeDecodeError):
                continue
            if "\n\n" in dump:
                exceptions = dump[dump.index("\n\n") + len("\n\n"):]
                try:
                    header = "exception throw location:\n"
                    stack = exceptions[exceptions.index(header) + len(header):]
                except ValueError:
                    continue
                # extract the first exception
                if dump.count(header) > 1:
                    stack = stack[:stack.index("\n\n")]
                pattern = re.compile(r"^\d+:[ ](.+)[ ]at[ ].+", re.M)
                roots = pattern.findall(stack)
                processed = Process(dump).internal_process()
                words = self.obtain_word(roots, processed)
                word_list.extend(words)
        Log().chart_print(Counter(word_list).most_common(10))

import re

from calculate import Calculate
from etl import ETL
from log import Log
from knowledge import Knowledge
from process import Process


class Detect:
    """
    Detect crash dump similarity through the mathematical model.
    Attributes:
        params: A pair of possible parameters (i.e., test_ids, dump_paths) that has crash failures.
    """
    def __init__(self, params):
        self.params = params

    def detect_sim(self):
        """
        Detect crash dump similarity and output the comparison result.
        """
        message = []
        order_pair, block_pair = [], []
        for param in self.params:
            # parameter is test_id
            if re.match(r"^\d{9,}$", param):
                dump = ETL().extract_cdb(param)
                processed = Process(dump).internal_process()
            # parameter is dump_path
            else:
                with open(param, "r", encoding="utf-8") as fp:
                    dump = fp.read()
                processed = Process(dump).pre_process()
            cpnt_order, func_block = Knowledge(processed).add_knowledge()
            message.extend([cpnt_order, func_block])
            order_pair.append(cpnt_order)
            block_pair.append(func_block)
        # output dump comparison
        Log().dump_print(message)
        Calculate(order_pair, block_pair).calculate_sim(debug=True)

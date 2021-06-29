import configparser
import os

from calculate import Calculate
from numpy import arange, array
from pool import MongoConnection
from sample import Sample
from sklearn.metrics import average_precision_score, precision_recall_curve


class Train:
    """
    Training for parameter tuning which contains data sampling.
    Attributes:
        dataset: The sampled dataset.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(os.getcwd(), "config.ini")
    config.read(config_path)
    # MongoDB
    host = config.get("mongodb", "host")
    port = config.getint("mongodb", "port")

    def __init__(self):
        self.dataset = Sample().sample_data()

    def predict_score(self, sample, m, n):
        """
        Calculate the predicted score for each sample.
        Args:
            sample: A sample in the dataset.
            m: The parameter for component position.
            n: The parameter for component distance.
        Returns:
            score: The predicted score.
        """
        with MongoConnection(self.host, self.port) as mongo:
            collection = mongo.connection["kdetector"]["dataset"]
            src = collection.find_one({"test_id": sample[0]})
            tgt = collection.find_one({"test_id": sample[1]})
            order_pair = [src["cpnt_order"], tgt["cpnt_order"]]
            block_pair = [src["func_block"], tgt["func_block"]]
        return Calculate(order_pair, block_pair).calculate_sim(m, n)

    def draw_curve(self, m, n):
        """
        Obtain basic information for curve drawing.
        Args:
            m: The parameter for component position.
            n: The parameter for component distance.
        Returns:
            The basic information, i.e., true label and predicted score.
        """
        true_label, pred_score = [], []
        for label, samples in enumerate(self.dataset):
            for sample in samples:
                score = self.predict_score(sample, m, n)
                true_label.append(label)
                pred_score.append(score)
        return array(true_label), array(pred_score)

    def debugging(self):
        """
        Output debugging information of training.
        """
        m = self.config.getfloat("model", "m")
        n = self.config.getfloat("model", "n")
        # obtain optimal cut-off point
        max_score = idx = 0
        true_label, pred_score = self.draw_curve(m, n)
        precision, recall, thresholds = precision_recall_curve(true_label, pred_score)
        for i in range(1, len(precision)):
            if precision[i] != precision[i-1]:
                # raise precision importance via F-Measure
                curr_score = (1 + 0.5 ** 2) * precision[i] * recall[i] / ((0.5 ** 2) * precision[i] + recall[i])
                if curr_score > max_score:
                    max_score, idx = curr_score, i
        threshold = thresholds[idx]
        print("\nThreshold={:.2%}".format(threshold))
        # output FP and FN
        for label, samples in enumerate(self.dataset):
            for sample in samples:
                score = self.predict_score(sample, m, n)
                if label == 0 and score >= threshold:
                    print("FP: {} {}".format(sample[0], sample[1]))
                if label == 1 and score < threshold:
                    print("FN: {} {}".format(sample[0], sample[1]))
        print("\n", end="")

    def training(self):
        """
        Obtain tuned parameters and update them to configuration file.
        """
        ap_max = m_opt = n_opt = 0.0
        print("Start parameter tuning...")
        for m in arange(0.0, 2.1, 0.1):
            for n in arange(0.0, 2.1, 0.1):
                true_label, pred_score = self.draw_curve(m, n)
                ap = average_precision_score(true_label, pred_score)
                print("m=%.1f, n=%.1f, AP=%.3f" % (m, n, ap))
                if ap > ap_max:
                    ap_max, m_opt, n_opt = ap, m, n
        print("\x1b[32mM_OPT=%.1f, N_OPT=%.1f, AP_MAX=%.3f\x1b[0m" % (m_opt, n_opt, ap_max))
        # update model parameters
        self.config.set("model", "m", "%.1f" % m_opt)
        self.config.set("model", "n", "%.1f" % n_opt)
        self.config.write(open(self.config_path, "w"))
        self.debugging()

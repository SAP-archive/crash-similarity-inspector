#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import urllib3

from detect import Detect
from etl import ETL
from stop_word import StopWord
from train import Train

parser = argparse.ArgumentParser()
parser.add_argument("--crawl", nargs="?", const=True, help="Crawling recent crash dumps.")
parser.add_argument("--train", nargs="?", const=True, help="Training for parameter tuning.")
parser.add_argument("--stop", nargs="?", const=True, help="Count file names that can be filtered.")
parser.add_argument("--detect", nargs=2, help="Detect crash dump similarity.")
args = parser.parse_args()
# suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if __name__ == "__main__":
    # crawling recent crash dumps
    if args.crawl:
        ETL().load()
    # training for parameter tuning
    if args.train:
        Train().training()
    # count file names that can be filtered
    if args.stop:
        StopWord().count_word()
    # detect crash dump similarity
    if args.detect:
        Detect(args.detect).detect_sim()

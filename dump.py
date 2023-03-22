#!/usr/bin/env python3
# Get all PMQs about mental health

from src.constants import TOPICS
from src.loksabha import LokSabhaQuestions
import os


def get_lsqs(download_path: str):
    # TODO support for multiple topics
    lsq = LokSabhaQuestions(download_path, TOPICS)
    lsq.get_qs()


# TODO add support for rajya sabha qs
def get_rsqs(download_path: str):
    pass


# TODO add support for sc/hc judgements
def get_sc_judgements(download_path: str):
    pass


if __name__ == "__main__":
    download_path = os.path.abspath(os.path.dirname(__file__))

    # Get lok sabha qs
    get_lsqs(download_path)

    # Get rajya sabha qs
    get_rsqs(download_path)

    # SC judgements
    get_sc_judgements(download_path)

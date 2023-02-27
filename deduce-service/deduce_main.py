import sys

import argparse
from datetime import datetime as dt

import deduce_app


if __name__ == '__main__':

    arguments = argparse.ArgumentParser(description='deduce_main: deidentifies a tab-delimited file using the '
                                                    'DEDUCE-framework')
    arguments.add_argument('--file_name', required= True, type=argparse.FileType('r'), help='Path to a tab-delimited file (UTF-8)')
    args = arguments.parse_args()
    file = args.file_name

    print("Processing file: ", file.name)
    current_time = dt.now()
    print("Start time: ", current_time)

    deduce_app.deidentify_tab_delimited_file(file.name, sys.stdout)

    current_time = dt.now()
    print("End time:   ", current_time)
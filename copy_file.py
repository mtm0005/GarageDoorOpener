#! /usr/local/bin/python3

import sys

def main():
    if len(sys.argv) != 3:
        sys.exit('Error: copy_file.py needs to be called with exactly 3 arguments')

    with open(sys.argv[1], 'r') as input_file:
        with open(sys.argv[2], 'w') as output_file:
            output_file.writelines(input_file.readlines())

if __name__ == '__main__':
    main()
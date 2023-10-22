import argparse
import logging
import tempfile
from sys import stdout

from module.ModelicaPackage import ModelicaClass

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', required=True, help='Path to input file')
    parser.add_argument('--outputdir', default=tempfile.gettempdir(), help='Path to output directory')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(stream=stdout, level=logging.DEBUG)

    # Log the arguments
    logging.info(f'Input file: {args.inputfile}')
    logging.info(f'Output directory: {args.outputdir}')

    with open(args.inputfile, 'r') as f:
        text = f.read()

    modelica_class = ModelicaClass(text)
    modelica_class()

    modelica_class.save(args.outputdir)

if __name__ == '__main__':
    main()
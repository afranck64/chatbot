import sys
import os
import argparse

if __name__ == "__main__":
    _path = os.path.split(__file__)[0]
    if _path:
        os.chdir(_path)
from src import analyse
import src.analyse as analyse
import src.learn as learn

def handler_analyse(args):
    if not learn.is_trained:
        sys.exit("The model has not been trained yet!\nPlease train the model using the command:\n\tpython main.py train")
    result = analyse.get_infos(args.sentence)
    print(f"Sentence: «{args.sentence}»")
    print(f"Analysis: {result}")

def handler_train(args):
    learn.learn()

def get_parser():
    parser = argparse.ArgumentParser(
        prog='python main.py',
        description='''
        '''

    )
    subparsers = parser.add_subparsers(
        title='commands',
        description='valid commands',
        help='additional help',
        required=True,
    )
    parser_analyse = subparsers.add_parser('analyse')
    parser_analyse.add_argument('sentence', type=str, help='sentence to analyse, should be passed in double quotes')
    parser_analyse.set_defaults(handler=handler_analyse)
    parser_train = subparsers.add_parser('train')
    parser_train.set_defaults(handler=handler_train)
    return parser


if __name__ == "__main__":
    parser = get_parser()
    if len(sys.argv) > 1:
        args = parser.parse_args()
        handler = args.handler
        handler(args)
    else:
        parser.print_help()

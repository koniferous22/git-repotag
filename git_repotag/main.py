from src.cli import cli, get_arg_parser
from src.logger import get_logger
import traceback
import sys

def main():
    try:
        parser = get_arg_parser()
        cli_result = cli(parser.parse_args())
        exit(cli_result)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        exit(1)

if __name__ == '__main__':
    main()

#!/usr/bin/python3
from argparse import ArgumentParser
from os import getcwd
from subprocess import run, PIPE
import sys
import os
import logging
from pathlib import Path, PurePosixPath
from pprint import pprint
from InquirerPy import inquirer
from InquirerPy.base import Choice


GITCONFIG_TAG_SECTION_DEFAULT = 'tag'
GITCONFIG_TAG_SECTION_ENV_VARIABLE = 'GITCONFIG_TAG_SECTION'


# Inspiration: https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
class LogFormatter(logging.Formatter):

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger(PurePosixPath(__file__).name)
logger.setLevel(logging.WARNING)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(LogFormatter())
logger.addHandler(ch)

def set_logging_level(level):
    ch.setLevel(level)
    logger.setLevel(level)

def path_exists(p):
    return p.expanduser().exists()

def is_git_repo(directory):
    git_dir = directory / '.git'
    return git_dir.exists()

def get_gitconfig_tag_section():
    gitconfig_tag_section_env = os.environ.get(GITCONFIG_TAG_SECTION_ENV_VARIABLE)
    return gitconfig_tag_section_env if gitconfig_tag_section_env is not None else GITCONFIG_TAG_SECTION_DEFAULT

def run_command(command, *, should_redirect_to_stdout=False, check=False):
    logger.info(f'Running command: "{command}" - {"exit" if check  else "continue"} on failure')
    stdout = sys.stdout if should_redirect_to_stdout else PIPE
    completed_process = run(command, shell=True, stdout=stdout, check=check)
    process_output = None if should_redirect_to_stdout else completed_process.stdout.decode('utf-8')
    return (completed_process.returncode, process_output)

def gitconfig_remove(tags, tag, repo_path):
    should_perform_cleanup = repo_path in tags.get(tag, [])
    # TODO analyze optional error throwing
    if should_perform_cleanup:
        run_command(
            f'git config --global --unset-all "{get_gitconfig_tag_section()}.{tag}" "{repo_path}"',
            should_redirect_to_stdout=True,
            check=True
        )

def gitconfig_add(tags, tag, repo_path):
    gitconfig_remove(tags, tag, repo_path)
    run_command(
        f'git config --global --add "{get_gitconfig_tag_section()}.{tag}" "{repo_path}"',
        should_redirect_to_stdout=True,
        check=True
    )
def gitconfig_parse_tags(*, should_print_repos=True):
    logger.info('Parsing tags from global .gitconfig')
    _, command_output = run_command(
        'git config --list',
        check=True
    )
    tag_section_prefix = f'{get_gitconfig_tag_section()}.'
    tag_config_entries = [ line[len(tag_section_prefix):] for line in command_output.splitlines() if line.startswith(tag_section_prefix) ]
    tag_entries = [ tuple(entry.split('=', 1)) for entry in tag_config_entries ]
    tag_dict = {}
    for tag, repo in tag_entries:
        tag_dict.setdefault(tag, []).append(repo)
    return tag_dict
    
def get_args():
    parser = ArgumentParser()
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group .add_argument('-v', action='store_const', dest='log_level', const=logging.INFO)
    verbosity_group .add_argument('-q', action='store_const', dest='log_level', const=logging.ERROR)
    subparsers = parser.add_subparsers(title='commands', dest='command', required=True)
    parser_add = subparsers.add_parser('add')
    parser_add.add_argument('tag', help='Gitconfig tag')
    parser_add.add_argument('path', nargs='?', help='Repo path')
    parser_remove = subparsers.add_parser('remove')
    parser_remove.add_argument('tag', help='Gitconfig tag')
    parser_remove.add_argument('path', nargs='?', help='Repo path')
    parser_interactive = subparsers.add_parser('interactive')
    parser_interactive.add_argument('path', nargs='?', help='Repo path')
    subparsers.add_parser('list')
    
    return parser.parse_args()

def validate_path(path):
    if not path_exists(path):
        return f'Path "{path}" does not exist'
    if not is_git_repo(path):
        return f'Path "{path}" is not a git repo'

def validate_tag(tag):
    if not tag.isalpha():
        return f'Tag "{tag}" contains invalid - non-alphabetic characters'

def add(tags ,tag, repo_path):
    logger.info('Running "add" command')
    validation_err = validate_path(repo_path)
    if validation_err is not None:
        raise Exception(validation_err)
    gitconfig_add(tags, tag, repo_path)

def remove(tags, tag, repo_path):
    validation_err = validate_path(repo_path)
    if validation_err is not None:
        raise Exception(validation_err)
    gitconfig_remove(tags, tag, repo_path)

def interactive(tags, repo_path):
    logger.info('Running "interactive" command')
    # Value has to be stringified, otherwise list lookup fails
    str_repo_path = str(repo_path)
    validation_err = validate_path(repo_path)
    if validation_err is not None:
        raise Exception(validation_err)
    modified_existing_tags = inquirer.checkbox(
        message='Select tags:',
        choices=[ Choice(tag, enabled=str_repo_path in repos) for tag,repos in tags.items() ],
        cycle=True,
    ).execute()
    should_add_new_tags = inquirer.confirm(message="Do you want to add extra tags?", default=False).execute()
    completely_new_tags = [tag.strip() for tag in inquirer.text(
        message='Enter tags (comma separated):',
        ).execute().split() ] if should_add_new_tags else []
    modified_existing_tags = set(modified_existing_tags)
    previous_existing_tags = set([tag for tag,repos in tags.items() if str_repo_path in repos])
    completely_new_tags = set(completely_new_tags)
    tags_defined_twice = (modified_existing_tags - previous_existing_tags) & completely_new_tags
    for tag in tags_defined_twice:
        logger.warning(f'Tag "{tag}" was defined on both inputs')
    tags_to_add = (modified_existing_tags - previous_existing_tags) | completely_new_tags
    tags_to_remove = previous_existing_tags - modified_existing_tags
    if not tags_to_add:
        logger.warning(f'No repository tags were added')
    for tag in tags_to_remove:
        logger.info(f'Removing tag "{tag}"')
        gitconfig_remove(tags, tag, repo_path)
    for tag in tags_to_add:
        logger.info(f'Adding tag "{tag}"')
        gitconfig_add(tags, tag, repo_path)


def list(tags, *, should_print_repos=False):
    logger.info('Running "list" command')
    if should_print_repos:
        pprint(tags)
    else:
        print('\n'.join(tags.keys()))

def main():
    try:
        args = get_args()
        if args.log_level is not None:
            set_logging_level(args.log_level)
        logger.info('Running in verbose mode')
        tags = gitconfig_parse_tags()
        if args.command == 'list':
            list(tags)
            return
        path = Path(args.path if args.path is not None else getcwd())
        path = path.expanduser().resolve()
        if args.command == 'add':
            add(tags, args.tag, path)
        elif args.command == 'remove':
            remove(tags, args.tag, path)
        elif args.command == 'interactive':
            interactive(tags, path)
        else:
            raise Exception(f'Unknown command "{args.command}"')
    except Exception as e:
        logger.error(e)
        exit(1)

main()

# TODO test when .gitconfig is empty
# TODO write unit test in a container, where git is installed

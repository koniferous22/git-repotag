#!/usr/bin/python3
from argparse import ArgumentParser
from os import getcwd
from subprocess import run, PIPE
import sys
import os
from pathlib import Path
from pprint import pprint
from InquirerPy import inquirer
from InquirerPy.base.control import Choice


GITCONFIG_TAG_SECTION_DEFAULT = 'tag'
GITCONFIG_TAG_SECTION_ENV_VARIABLE = 'GITCONFIG_TAG_SECTION'

def path_exists(p):
    return p.expanduser().exists()

def is_git_repo(directory):
    git_dir = directory / '.git'
    return git_dir.exists()

def get_gitconfig_tag_section():
    gitconfig_tag_section_env = os.environ.get(GITCONFIG_TAG_SECTION_ENV_VARIABLE)
    return gitconfig_tag_section_env if gitconfig_tag_section_env is not None else GITCONFIG_TAG_SECTION_DEFAULT

# TODO verbose commands
def run_command(command, *, should_redirect_to_stdout=False, check=False):
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
    

def git_config_is_tagged(tag, repo_path):
    pass

def get_args():
    parser = ArgumentParser()
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
    validation_err = validate_path(repo_path)
    if validation_err is not None:
        raise Exception(validation_err)
    user_existing_tags = inquirer.checkbox(
        message='Select tags:',
        choices=[ tag for tag in tags.keys() ],
        cycle=True,
    ).execute()
    should_add_new_tags = inquirer.confirm(message="Do you want to add extra tags?", default=False).execute()
    user_new_tags = [tag.strip() for tag in inquirer.text(
        message='Enter tags (comma separated):',
        ).execute().split() ] if should_add_new_tags else []
    tags_to_add = set(user_existing_tags) | set(user_new_tags)
    for tag in tags_to_add:
        gitconfig_add(tags, tag, repo_path)
    # TODO add warning when no tags have been added
    # TODO add warning when tag is added on two places

def list(tags, *, should_print_repos=False):
    if should_print_repos:
        pprint(tags)
    else:
        print('\n'.join(tags.keys()))

def main():
    args = get_args()
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

main()

# TODO colored output
# TODO verbose mode
# TODO error handling

# TODO test when .gitconfig is empty
# TODO unit test

# TODO config

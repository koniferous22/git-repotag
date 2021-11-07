#!/usr/bin/python3
from argparse import ArgumentParser
from os import getcwd
import logging
from pathlib import Path
from pprint import pprint
from InquirerPy import inquirer
from InquirerPy.base import Choice

from . import GIT_DIR, set_logging_level, get_logger, gitconfig_parse_repotags, gitconfig_add, gitconfig_remove

def path_exists(p):
    return p.expanduser().exists()

def is_git_repo(directory):
    git_dir = directory / GIT_DIR
    return git_dir.exists()

def get_arg_parser():
    parser = ArgumentParser('git-repotag')
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group .add_argument('-v', help='Verbose', action='store_const', dest='log_level', const=logging.INFO)
    verbosity_group .add_argument('-q', help='Quiet', action='store_const', dest='log_level', const=logging.ERROR)
    subparsers = parser.add_subparsers(title='commands', dest='command', required=True)
    parser_add = subparsers.add_parser('add', help='Add tag to git repo')
    parser_add.add_argument('tag', help='Gitconfig tag')
    parser_add.add_argument('path', nargs='?', help='Repo path')
    parser_remove = subparsers.add_parser('remove', help='Removes tag from repo')
    parser_remove.add_argument('tag', help='Gitconfig tag')
    parser_remove.add_argument('path', nargs='?', help='Repo path')
    parser_interactive = subparsers.add_parser('interactive', help='Runs inquirerpy prompt')
    parser_interactive.add_argument('path', nargs='?', help='Repo path')
    parser_list = subparsers.add_parser('list', help='Lists objects')
    subparsers_list = parser_list.add_subparsers(title='list subcommand', dest='list_subcommand', required=True)
    parser_list_tags = subparsers_list.add_parser('tags', help='Lists tags')
    parser_list_tags.add_argument('-p', '--pprint', action='store_true', help='Pretty print output')
    parser_list_repos = subparsers_list.add_parser('repos', help='Lists repos')
    parser_list_repos.add_argument('-p', '--pprint', action='store_true', help='Pretty print output')
    subparsers.add_parser('validate', help="Checks for invalid paths in gitconfig")
    parser_cleanup = subparsers.add_parser('cleanup', help="Cleanup of invalid paths in gitconfig")
    parser_cleanup.add_argument('-y', help='Assume yes for prompts', dest='assume_yes', action='store_true')
    return parser

def validate_path(path):
    if not path_exists(path):
        return f'Path "{path}" does not exist'
    if not is_git_repo(path):
        return f'Path "{path}" is not a git repo'

def validate_tag(tag):
    if not tag.isalpha():
        return f'Tag "{tag}" contains invalid - non-alphabetic characters'

def add(repotags ,tag, repo_path):
    get_logger().info('Running "add" command')
    validation_err = validate_path(repo_path)
    if validation_err is not None:
        raise Exception(validation_err)
    gitconfig_add(repotags, tag, repo_path)

def remove(repotags, tag, repo_path):
    validation_err = validate_path(repo_path)
    if validation_err is not None:
        raise Exception(validation_err)
    gitconfig_remove(repotags, tag, repo_path)

def interactive(repotags, repo_path):
    get_logger().info('Running "interactive" command')
    # Value has to be stringified, otherwise list lookup fails
    str_repo_path = str(repo_path)
    validation_err = validate_path(repo_path)
    if validation_err is not None:
        raise Exception(validation_err)
    modified_existing_repotags = inquirer.checkbox(
        message='Select tags:',
        choices=[ Choice(tag, enabled=str_repo_path in repos) for tag,repos in repotags.items() ],
        cycle=True,
    ).execute()
    should_add_new_repotags = inquirer.confirm(message="Do you want to add extra tags?", default=False).execute()
    completely_new_repotags = [tag.strip() for tag in inquirer.text(
        message='Enter tags (comma separated):',
        ).execute().split() ] if should_add_new_repotags else []
    modified_existing_repotags = set(modified_existing_repotags)
    previous_existing_repotags = set([tag for tag,repos in repotags.items() if str_repo_path in repos])
    completely_new_repotags = set(completely_new_repotags)
    repotags_defined_twice = (modified_existing_repotags - previous_existing_repotags) & completely_new_repotags
    for tag in repotags_defined_twice:
        get_logger().warning(f'Tag "{tag}" was defined on both inputs')
    repotags_to_add = (modified_existing_repotags - previous_existing_repotags) | completely_new_repotags
    repotags_to_remove = previous_existing_repotags - modified_existing_repotags
    if not repotags_to_add:
        get_logger().warning(f'No repository tags were added')
    for tag in repotags_to_remove:
        get_logger().info(f'Removing tag "{tag}"')
        gitconfig_remove(repotags, tag, repo_path)
    for tag in repotags_to_add:
        get_logger().info(f'Adding tag "{tag}"')
        gitconfig_add(repotags, tag, repo_path)


def get_repotags_by_repos(repotags):
    tag_repo_items = [ (tag, repo) for tag, repos in repotags.items() for repo in repos]
    repotags_by_repos = {}
    for tag, repo in tag_repo_items:
        if not repo in repotags_by_repos:
            repotags_by_repos[repo] = []
        repotags_by_repos[repo].append(tag)
    return repotags_by_repos

def list_tags(repotags, *, should_pprint=False):
    get_logger().info('Running "list_tags" command')
    if should_pprint:
        pprint(repotags)
    else:
        print('\n'.join(repotags.keys()))

def list_repos(repotags, *, should_pprint=False):
    get_logger().info('Running "list_repos" command')
    repotags_by_repos = get_repotags_by_repos(repotags)
    if should_pprint:
        pprint(repotags_by_repos)
    else:
        for repo, tags in repotags_by_repos.items():
            print(f'{repo} tags: {tags}')


def validate(repotags):
    get_logger().info('Running "validate" command')
    repotags_by_repos = get_repotags_by_repos(repotags)
    command_result = 0
    for repo, repotags in repotags_by_repos.items():
        validation_error = validate_path(Path(repo))
        if validation_error:
            get_logger().warning(f'{validation_error} (tags: {repotags})')
            command_result = 1
    return command_result

def cleanup(repotags, assume_yes=False):
    get_logger().info('Running "cleanup" command')
    repotags_by_repos = get_repotags_by_repos(repotags)
    for repo, tags in repotags_by_repos.items():
        validation_error = validate_path(Path(repo))
        if validation_error:
            should_perform_cleanup = assume_yes or inquirer.confirm(message=f"{validation_error}\nRemove for tags: {tags}?", default=False).execute()
            if should_perform_cleanup:
                for tag in tags:
                    gitconfig_remove(repotags, tag, repo)

def get_path_from_args(args):
    path = Path(args.path if args.path is not None else getcwd())
    return path.expanduser().resolve()

def cli(args):
    if args.log_level is not None:
        set_logging_level(args.log_level)
    get_logger().info('Running in verbose mode')
    repotags = gitconfig_parse_repotags()
    cli_result = 0
    if args.command == 'list':
        if args.list_subcommand == 'tags':
            list_tags(repotags, should_pprint=args.pprint)
        elif args.list_subcommand == 'repos':
            list_repos(repotags, should_pprint=args.pprint)
        else:
            raise Exception(f'Unknown subcommand "{args.command} {args.list_subcommand}"')
    elif args.command == 'add':
        path = get_path_from_args(args)
        add(repotags, args.tag, path)
    elif args.command == 'remove':
        path = get_path_from_args(args)
        remove(repotags, args.tag, path)
    elif args.command == 'interactive':
        path = get_path_from_args(args)
        interactive(repotags, path)
    elif args.command == 'validate':
        # Apply exit code from the result
        cli_result = validate(repotags)
    elif args.command == 'cleanup':
        cleanup(repotags, args.assume_yes)
    else:
        raise Exception(f'Unknown command "{args.command}"')
    return cli_result


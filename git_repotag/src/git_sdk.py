import sys
import os
from subprocess import PIPE, run
from pprint import pprint
from .config import GITCONFIG_TAG_SECTION_DEFAULT, GITCONFIG_TAG_SECTION_ENV_VARIABLE
from .logger import get_logger

def get_gitconfig_tag_section():
    gitconfig_tag_section_env = os.environ.get(GITCONFIG_TAG_SECTION_ENV_VARIABLE)
    return gitconfig_tag_section_env if gitconfig_tag_section_env is not None else GITCONFIG_TAG_SECTION_DEFAULT

def run_command(command, *, should_redirect_to_stdout=False, check=False):
    get_logger().info(f'Running command: "{command}" - {"exit" if check  else "continue"} on failure')
    stdout = sys.stdout if should_redirect_to_stdout else PIPE
    completed_process = run(command, shell=True, stdout=stdout, check=check)
    process_output = None if should_redirect_to_stdout else completed_process.stdout.decode('utf-8')
    return (completed_process.returncode, process_output)

def gitconfig_remove(repotags, tag, repo_path):
    repo_path_string=  str(repo_path)
    should_perform_cleanup = repo_path_string in repotags.get(tag, [])
    # TODO analyze optional error throwing
    if should_perform_cleanup:
        run_command(
            f'git config --global --unset-all "{get_gitconfig_tag_section()}.{tag}" "{repo_path_string}"',
            should_redirect_to_stdout=True,
            check=True
        )

def gitconfig_add(repotags, tag, repo_path):
    gitconfig_remove(repotags, tag, repo_path)
    run_command(
        f'git config --global --add "{get_gitconfig_tag_section()}.{tag}" "{repo_path}"',
        should_redirect_to_stdout=True,
        check=True
    )

def gitconfig_parse_repotags(*, should_print_repos=True):
    get_logger().info('Parsing tags from global .gitconfig')
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
    

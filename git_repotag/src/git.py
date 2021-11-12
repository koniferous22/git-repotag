import sys
import os
from subprocess import PIPE, run

from .exception import AppException
from .config import (
    EXTRA_GITCONFIG_FILE_DEFAULT,
    EXTRA_GITCONFIG_FILE_ENV_VARIABLE,
    GITCONFIG_TAG_SECTION_DEFAULT,
    GITCONFIG_TAG_SECTION_ENV_VARIABLE,
)
from .logger import get_logger


def run_command(command, *, should_redirect_to_stdout=False, check=False):
    get_logger().info(
        f'Running command: "{command}" - {"exit" if check  else "continue"} on failure'
    )
    stdout = sys.stdout if should_redirect_to_stdout else PIPE
    completed_process = run(command, shell=True, stdout=stdout, check=check)
    process_output = (
        None if should_redirect_to_stdout else completed_process.stdout.decode("utf-8")
    )
    return (completed_process.returncode, process_output)


def parse_git_config_key_value(prefix, *, file_option=""):
    get_logger().info(
        f'Parsing "{prefix}" from .gitconfig{f" (file option - {file_option})" if file_option else ""}'
    )
    _, command_output = run_command(f"git config {file_option} --list", check=True)
    tag_config_entries = [
        line for line in command_output.splitlines() if line.startswith(prefix)
    ]
    return [tuple(entry.split("=", 1)) for entry in tag_config_entries]


def get_extra_gitconfig_file():
    extra_gitconfig_file_location_env = os.environ.get(
        EXTRA_GITCONFIG_FILE_ENV_VARIABLE
    )
    extra_gitconfig_file_location = (
        extra_gitconfig_file_location_env
        if extra_gitconfig_file_location_env is not None
        else EXTRA_GITCONFIG_FILE_DEFAULT
    )
    extra_gitconfig_file_entries = parse_git_config_key_value(
        extra_gitconfig_file_location, file_option="--global"
    )
    if not extra_gitconfig_file_entries:
        return
    if len(extra_gitconfig_file_entries) > 1:
        raise AppException("Encountered more than gitconfig file for tags")
    return extra_gitconfig_file_entries[0][1]


def get_gitconfig_tag_section():
    gitconfig_tag_section_env = os.environ.get(GITCONFIG_TAG_SECTION_ENV_VARIABLE)
    return (
        gitconfig_tag_section_env
        if gitconfig_tag_section_env is not None
        else GITCONFIG_TAG_SECTION_DEFAULT
    )


def get_file_option_from_maybe_extra_gitconfig(extra_gitconfig=None):
    # NOTE: both single & double quotes don't work with --file option, therefore no escaping is performed
    return "--global" if extra_gitconfig is None else f"--file {extra_gitconfig}"


def gitconfig_remove(repotags, tag, repo_path, extra_gitconfig=None):
    file_option = get_file_option_from_maybe_extra_gitconfig(extra_gitconfig)
    repo_path_string = str(repo_path)
    should_perform_cleanup = repo_path_string in repotags.get(tag, [])
    if should_perform_cleanup:
        run_command(
            f'git config {file_option} --unset-all "{get_gitconfig_tag_section()}.{tag}" "{repo_path_string}"',
            should_redirect_to_stdout=True,
            check=True,
        )


def gitconfig_add(repotags, tag, repo_path, extra_gitconfig=None):
    file_option = get_file_option_from_maybe_extra_gitconfig(extra_gitconfig)
    gitconfig_remove(repotags, tag, repo_path, extra_gitconfig)
    run_command(
        f'git config {file_option} --add "{get_gitconfig_tag_section()}.{tag}" "{repo_path}"',
        should_redirect_to_stdout=True,
        check=True,
    )


def gitconfig_parse_repotags(*, extra_gitconfig=None):
    file_option = get_file_option_from_maybe_extra_gitconfig(extra_gitconfig)
    get_logger().info('Parsing tags from "{file_option}" .gitconfig')
    _, command_output = run_command(f"git config {file_option} --list", check=True)
    tag_section_prefix = f"{get_gitconfig_tag_section()}."
    tag_config_entries = [
        line[len(tag_section_prefix) :]
        for line in command_output.splitlines()
        if line.startswith(tag_section_prefix)
    ]
    tag_entries = [tuple(entry.split("=", 1)) for entry in tag_config_entries]
    tag_dict = {}
    for tag, repo in tag_entries:
        tag_dict.setdefault(tag, []).append(repo)
    return tag_dict

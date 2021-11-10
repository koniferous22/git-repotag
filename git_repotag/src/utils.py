from .config import GIT_DIR

def path_exists(p):
    return p.expanduser().exists()

def is_git_repo(directory):
    git_dir = directory / GIT_DIR
    return git_dir.exists()

def validate_path(path):
    if not path_exists(path):
        return f'Path "{path}" does not exist'
    if not is_git_repo(path):
        return f'Path "{path}" is not a git repo'


def validate_tag(tag):
    if not tag.isalpha():
        return f'Tag "{tag}" contains invalid - non-alphabetic characters'

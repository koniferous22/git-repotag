#!/usr/bin/python3
import unittest
import os
import logging
from git_repotag.src.git import gitconfig_add, gitconfig_parse_repotags, run_command
from git_repotag.src.cli import cli, get_arg_parser
from git_repotag.src.logger import set_logging_level

set_logging_level(logging.CRITICAL)

class GitRepotagTest(unittest.TestCase):

    gitconfig_path = os.environ.get('GITCONFIG_PATH')
    arg_parser = get_arg_parser()

    # If necessary add setup method to create .gitconfig
    # Also with cleanup method that will remove .gitconfig

    def test_cleanup(self):
        gitconfig_add({}, 'tag1', '/not/a/repo')
        args_validate = self.arg_parser.parse_args(['validate'])
        self.assertNotEqual(cli(args_validate), 0, 'Expected validation to fail')
        args_cleanup = self.arg_parser.parse_args(['cleanup', '-y'])
        self.assertEqual(cli(args_cleanup), 0, 'Expected cleanup to succeed')
        self.assertEqual(gitconfig_parse_repotags(), {}, 'Expected empty repotags in gitconfig')
        

    def test_add_remove(self):
        repo1_path = '/repos/repo1'
        not_a_repo_path = '/repos/not-a-repo'
        run_command(f'mkdir -p {repo1_path}', should_redirect_to_stdout=True)
        run_command(f'cd {repo1_path} && git init', should_redirect_to_stdout=True)
        run_command(f'mkdir {not_a_repo_path}', should_redirect_to_stdout=True)
        test_tag = 'tag'
        args_add_repo1 = self.arg_parser.parse_args(['add', test_tag, repo1_path])
        self.assertEqual(cli(args_add_repo1), 0, 'Expected adding repo to succeed')
        args_remove_repo1 = self.arg_parser.parse_args(['remove', test_tag, repo1_path])
        self.assertEqual(cli(args_remove_repo1), 0, 'Expected removing repo to succeed')
        args_add_not_repo = self.arg_parser.parse_args(['add', test_tag, not_a_repo_path])
        with self.assertRaises(Exception):
            cli(args_add_not_repo)
if __name__ == '__main__':
    unittest.main()

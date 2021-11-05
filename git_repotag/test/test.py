#!/usr/bin/python3
import unittest
import os
import sys
from git_repotag.src.git_sdk import gitconfig_parse_repotags

print(gitconfig_parse_repotags())

class TestStringMethods(unittest.TestCase):

    gitconfig_path = os.environ.get('GITCONFIG_PATH')

    # def test_cleanup(self):
    #     pass

    def test_add_remove(self):
        self.assertEqual('foo'.upper(), 'FOO')

if __name__ == '__main__':
    unittest.main()

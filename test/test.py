#!/usr/bin/python3
import unittest
import os

class TestStringMethods(unittest.TestCase):

    gitconfig_path = os.environ.get('GITCONFIG_PATH')

    # def test_cleanup(self):
    #     pass

    def test_add_remove(self):
        self.assertEqual('foo'.upper(), 'FOO')

if __name__ == '__main__':
    unittest.main()

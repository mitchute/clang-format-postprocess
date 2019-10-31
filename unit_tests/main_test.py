import unittest
import tempfile
import os

from src.process_clang import ClangPostProcess

class TestMain(unittest.TestCase):

    @staticmethod
    def add_instance():
        source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cpp")
        return ClangPostProcess(source_dir)

    def test_main(self):
        tst = self.add_instance()
        tst.process()
        i = 1

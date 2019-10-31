import fnmatch
import logging
import os


class Base(object):
    def __init__(self, source_dir, list_file=None, output_dir=None):

        logging.basicConfig(filename='clang-post-process.log',
                            filemode='w',
                            format='%(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        self.src_dir = source_dir
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = "output.csv"

        # read files from list file if present
        files_from_list = []
        if list_file:
            with open(list_file, 'r') as f:
                for line in f:
                    files_from_list.append(line.strip("\n"))

        self.files_from_list = files_from_list.copy()

        # load files to run
        self.files = []
        self.file_names = []
        for root, dirs, walk_files in os.walk(self.src_dir):
            for file in walk_files:
                if fnmatch.fnmatch(file, "*.cc") or fnmatch.fnmatch(file, "*.cpp"):
                    f_path = os.path.abspath(os.path.join(root, file))
                    if list_file and file in files_from_list:
                        self.files.append(f_path)
                        self.file_names.append(f_path.split("/")[-1])
                        logging.info("'{}' added to run".format(f_path))
                        files_from_list.remove(file)
                    elif list_file and file not in files_from_list:
                        pass
                    elif not list_file:
                        self.files.append(f_path)
                        self.file_names.append(f_path.split("/")[-1])
                        logging.info("'{}' added to run".format(f_path))
                    else:
                        logging.error("Unknown error condition")

        if len(files_from_list) > 0:
            for file in files_from_list:
                logging.error("'{}' file not found - skipping".format(file))

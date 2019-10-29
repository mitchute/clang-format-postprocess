import argparse
import fnmatch
import logging
import os
import subprocess

from collections import defaultdict


class ClangPostProcess(object):
    def __init__(self, build_dir, src_dir, list_file=None):

        logging.basicConfig(filename='clang-post-process.log',
                            filemode='w',
                            format='%(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        self.build_dir = build_dir
        self.src_dir = src_dir

        class Method(object):
            def __init__(self):
                self.name = None
                self.exe = None

        self.global_storage = Method()
        self.has_local_qualifiers = Method()
        self.has_local_storage = Method()
        self.is_static_storage_cls = Method()

        # check hasGlobalStorage
        self.global_storage.name = "global-detect-hasGlobalStorage"
        self.global_storage.exe = os.path.join(self.build_dir, "apps", self.global_storage.name)

        if not os.path.exists(self.global_storage.exe):
            raise SystemExit("'{}' exe does not exist".format(self.global_storage.name))
        else:
            logging.info("'{}' exe found".format(self.global_storage.name))

        # check hasLocalQualifiers
        self.has_local_qualifiers.name = "global-detect-hasLocalQualifiers"
        self.has_local_qualifiers.exe = os.path.join(self.build_dir, "apps", self.has_local_qualifiers.name)

        if not os.path.exists(self.has_local_qualifiers.exe):
            raise SystemExit("'{}' exe does not exist".format(self.has_local_qualifiers.name))
        else:
            logging.info("'{}' exe found".format(self.has_local_qualifiers.name))

        # check hasLocalStorage
        self.has_local_storage.name = "global-detect-hasLocalStorage"
        self.has_local_storage.exe = os.path.join(self.build_dir, "apps", self.has_local_storage.name)

        if not os.path.exists(self.has_local_storage.exe):
            raise SystemExit("'{}' exe does not exist".format(self.has_local_storage.name))
        else:
            logging.info("'{}' exe found".format(self.has_local_storage.name))

        # check isStaticStorageClass
        self.is_static_storage_cls.name = "global-detect-isStaticStorageClass"
        self.is_static_storage_cls.exe = os.path.join(self.build_dir, "apps", self.is_static_storage_cls.name)

        if not os.path.exists(self.is_static_storage_cls.exe):
            raise SystemExit("'{}' exe does not exist".format(self.is_static_storage_cls.name))
        else:
            logging.info("'{}' exe found".format(self.is_static_storage_cls.name))

        # read files from list file if present
        files_from_list = []
        if list_file:
            with open(list_file, 'r') as f:
                for line in f:
                    files_from_list.append(line.strip("\n"))

        # load files to run
        self.files = []
        for root, dirs, walk_files in os.walk(self.src_dir):
            for file in walk_files:
                if fnmatch.fnmatch(file, "*.cc"):
                    f_path = os.path.abspath(os.path.join(root, file))
                    if list_file and file in files_from_list:
                        self.files.append(f_path)
                        logging.info("'{}' added to run".format(f_path))
                        files_from_list.remove(file)
                    elif list_file and file not in files_from_list:
                        pass
                    elif not list_file:
                        self.files.append(f_path)
                        logging.info("'{}' added to run".format(f_path))
                    else:
                        logging.error("Unknown error condition")

        if len(files_from_list) > 0:
            for file in files_from_list:
                logging.error("'{}' file not found - skipping".format(file))

    @staticmethod
    def run_exe(caller, exe_path, f_path):
        args = ["-p",
                "/Users/mmitchel/Projects/EnergyPlus/dev/develop/cmake-build-debug",
                "-extra-arg=-I/usr/local/opt/llvm@7/include/c++/",
                "-extra-arg=-I/usr/local/opt/llvm@7/include/c++/v1",
                "-extra-arg=-I/usr/local/opt/llvm@7//lib/clang/7.0.0/include/",
                "-extra-arg=-I/usr/local/opt/llvm@7/lib/clang/7.1.0/include",
                "{}".format(f_path)]

        logging.debug(" ".join([exe_path,
                                args[0],
                                args[1],
                                args[2],
                                args[3],
                                args[4],
                                args[5],
                                args[6]]))

        try:
            return subprocess.check_output([exe_path,
                                            args[0],
                                            args[1],
                                            args[2],
                                            args[3],
                                            args[4],
                                            args[5],
                                            args[6]],
                                           shell=False)
        except:
            f_name = f_path.split("/")[-1]
            logging.info("Failed on caller: '{}' for file: {}".format(caller, f_name))

    def run_has_global_storage(self, f_path):
        logging.info("Running: {}".format(self.global_storage.name))
        return self.run_exe(self.global_storage.name, self.global_storage.exe, f_path)

    def run_has_local_qualifiers(self, f_path):
        logging.info("Running: {}".format(self.has_local_qualifiers.name))
        return self.run_exe(self.has_local_qualifiers.name, self.has_local_qualifiers.exe, f_path)

    def run_has_local_storage(self, f_path):
        logging.info("Running: {}".format(self.has_local_storage.name))
        return self.run_exe(self.has_local_storage.name, self.has_local_storage.exe, f_path)

    def run_is_static_storage_class(self, f_path):
        logging.info("Running: {}".format(self.is_static_storage_cls.name))
        return self.run_exe(self.is_static_storage_cls.name, self.is_static_storage_cls.exe, f_path)

    def process_output(self, stream, f_path):
        f_name = f_path.split('/')[-1]
        lines = stream.decode('utf-8').split('\n')
        start_idx = 0
        for line in lines:
            if f_name in line:
                break
            start_idx += 1
        var_lst = []
        for idx in range(start_idx, len(lines) - 1):
            line = lines[idx]
            var_lst.append(self.process_line(line))
        return var_lst

    @staticmethod
    def process_line(line):
        line = line.replace("\'", "\"")

        name = line.split("\"")[1]
        namespace = ""
        if "::" in name:
            tokens = name.split("::")
            name = tokens[-1]
            namespace = tokens[-2]

        position_str = line.split("<")[1]
        position_str = position_str.split(">")[0]

        if ".cc" in position_str:
            line_no = position_str.split(":")[1]
        elif "line" in position_str:
            line_no = position_str.split(":")[1]
        else:
            line_no = None

        d = {"name": name, "namespace": namespace, "line": line_no}

        if "is static local:" in line:
            static_local = int(line.split(":")[-1].strip())
            if static_local == 1:
                d["is-static"] = True

        return d

    def process_global_storage(self, stream, f_path):
        lst = self.process_output(stream, f_path)
        for d in lst:
            d["has-global-storage"] = True
        return lst

    def process_has_local_qualifiers(self, stream, f_path):
        lst = self.process_output(stream, f_path)
        for d in lst:
            d["has-local-qualifier"] = True
        return lst

    def process_single_file(self, f_path):
        glob_store_lst = self.process_global_storage(self.run_has_global_storage(f_path), f_path)
        local_quals_lst = self.process_has_local_qualifiers(self.run_has_local_qualifiers(f_path), f_path)
        return self.merge_lists(glob_store_lst, local_quals_lst)

    @staticmethod
    def merge_lists(*args):
        main_lst = []
        for lst_num, var_lst in enumerate(args):
            for d_var in var_lst:
                var_merged = False
                if lst_num == 0:
                    pass
                else:
                    for main_idx, d_var_main in enumerate(main_lst):
                        if (d_var_main["name"] == d_var["name"]) and (d_var_main["line"] == d_var["line"]):
                            main_lst[main_idx] = {**d_var_main, **d_var}
                            var_merged = True
                if not var_merged:
                    main_lst.append(d_var)

        for idx, d in enumerate(main_lst):
            main_lst[idx] = defaultdict(str, d)
        return main_lst

    def process(self):
        with open("output.csv", "a+") as f:
            f.write("var-name,namespace,line-no,is-static,has-local-qualifier,has-global-storage\n")
            for file in self.files:
                try:
                    logging.info("{} : started".format(file))
                    summary = self.process_single_file(file)
                    for val in summary:
                        f.write("{},{},{},{},{},{}\n".format(val["name"],
                                                             val["namespace"],
                                                             val["line"],
                                                             val['is-static'],
                                                             val['has-local-qualifier'],
                                                             val['has-global-storage']))

                    logging.info("{} : completed".format(file))
                except:
                    logging.info("{} : failed".format(file))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('-b', dest="build_dir", help="path to the clang-format build dir")
    parser.add_argument('-s', dest="source_dir", help="path to the EnergyPlus /src/EnergyPlus dir")
    parser.add_argument('-l', dest="list_file",
                        help="(optional) path to list file with .cc file names to process. If list file not given, "
                             "all .cc files in /src/EnergyPlus will be processed.")

    results = parser.parse_args()

    if results.build_dir is None:
        raise SystemExit("build-dir '-b' argument required")
    elif results.source_dir is None:
        raise SystemExit("source-dir '-s' argument required")
    elif results.list_file is None:
        P = ClangPostProcess(results.build_dir, results.source_dir)
        P.process()
    else:
        P = ClangPostProcess(results.build_dir, results.source_dir, results.list_file)
        P.process()

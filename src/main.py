import argparse
import fnmatch
import os
import subprocess


class ClangPostProcess(object):
    def __init__(self, *args):
        self.build_dir = args[1]

    @staticmethod
    def run_exe(caller, exe_path, f_path):
        args = ["-p",
                "/Users/mmitchel/Projects/EnergyPlus/dev/develop/cmake-build-debug",
                "-extra-arg=-I/usr/local/opt/llvm@7/include/c++/",
                "-extra-arg=-I/usr/local/opt/llvm@7/include/c++/v1",
                "-extra-arg=-I/usr/local/opt/llvm@7//lib/clang/7.0.0/include/",
                "-extra-arg=-I/usr/local/opt/llvm@7/lib/clang/7.1.0/include",
                "{}".format(f_path)]

        print(" ".join([exe_path,
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
            print("Failed on caller: '{}' for file: {}".format(caller, f_name))

    def run_has_global_storage(self, f_path):
        exe_path = "/Users/mmitchel/Projects/clang-refactor/build/apps/global-detect-hasGlobalStorage"
        return self.run_exe("hasGlobalStorage", exe_path, f_path)

    def run_has_local_qualifiers(self, f_path):
        exe_path = "/Users/mmitchel/Projects/clang-refactor/build/apps/global-detect-hasLocalQualifiers"
        return self.run_exe("hasLocalQualifiers", exe_path, f_path)

    def run_has_local_storage(self, f_path):
        exe_path = "/Users/mmitchel/Projects/clang-refactor/build/apps/global-detect-hasLocalStorage"
        return self.run_exe("hasLocalStorage", exe_path, f_path)

    def run_is_static_storage_class(self, f_path):
        exe_path = "/Users/mmitchel/Projects/clang-refactor/build/apps/global-detect-isStaticStorageClass"
        return self.run_exe("isStaticStorageClass", exe_path, f_path)

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
        print(line)

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
            line_no = 0

        d = {"name": name,
             "namespace": namespace,
             "line": line_no}

        if "is static local:" in line:
            static_local = line.split(":")[-1]
            if static_local == 1:
                d["static-local"] = True

        return d

    def process_global_storage(self, stream, f_path):
        glob_lst = self.process_output(stream, f_path)
        for entry in glob_lst:
            entry["has-global-storage"] = True
        return glob_lst

    def process_single_file(self, f_path):
        glob_store_lst = self.process_global_storage(self.run_has_global_storage(f_path), f_path)
        return self.merge_lists(glob_store_lst)

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
        return main_lst

    def process_all(self):
        cc_dir = "/Users/mmitchel/Projects/EnergyPlus/dev/develop/src/EnergyPlus"
        for root, dirs, files in os.walk(cc_dir):
            for file in files:
                if fnmatch.fnmatch(file, "*.cc"):
                    try:
                        var_list = self.process_single_file(os.path.abspath(os.path.join(root, file)))
                        with open("output.csv", "a+") as f:
                            for entry in var_list:
                                f.write("{},{},{}\n".format(entry["name"], entry["namespace"], entry["line"]))
                        print("{} : completed".format(file))
                    except:
                        print("{} : failed".format(file))
                    break
                break


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
        P = ClangPostProcess(results.build_dir, results.src_dir)
        P.process_all()
    else:
        P = ClangPostProcess(results.build_dir, results.src_dir, results.list_file)
        P.process_all()

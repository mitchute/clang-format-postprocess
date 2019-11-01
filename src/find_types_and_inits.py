import argparse
import json
import logging

from src.base import Base


class TypeInitFinder(Base):
    def __init__(self, source_dir, preprocess_csv, list_file=None, output_dir=None):
        Base.__init__(self, source_dir=source_dir, list_file=list_file, output_dir=output_dir)
        self.preprocess_csv = preprocess_csv
        self.d_files = []

        # make list of dicts for each file
        for idx, file in enumerate(self.files):
            f_name = file.split("/")[-1]
            d = {"file-name": f_name, "path": file}
            self.d_files.append(d)

        # pars variables to process into dict for each file
        with open(self.preprocess_csv, 'r') as f:
            for idx, line in enumerate(f):
                if idx == 0:
                    pass
                else:
                    tokens = line.split(",")
                    f_name = tokens[0]
                    namespace = tokens[2]
                    if f_name in self.file_names and namespace is not "":
                        var = tokens[1]
                        line_no = int(tokens[3])
                        file_idx = self.get_file_idx(f_name)
                        d = {"name": var, "namespace": namespace, "line-no": line_no}
                        if "vars" in self.d_files[file_idx]:
                            self.d_files[file_idx]["vars"].append(d)
                        else:
                            self.d_files[file_idx]["vars"] = [d]

        # sort vars by line number
        for idx, d in enumerate(self.d_files):
            if "vars" in self.d_files[idx]:
                self.d_files[idx]['vars'] = sorted(d['vars'], key=lambda i: (i['line-no']))

    def get_file_idx(self, f_name):
        for idx, d in enumerate(self.d_files):
            if f_name == d["file-name"]:
                return idx

    @staticmethod
    def get_cpp_data(all_lines, start_line_no):

        cpp_type = ''
        init_val = ''
        is_const = False
        is_static = False
        raw_cpp = ''

        # get raw cpp in single line
        for idx in range(start_line_no, len(all_lines)):
            this_line = all_lines[idx]
            if "//" in this_line:
                this_line = this_line.split("//")[0]
            this_line = this_line.replace("\n", "").strip()
            raw_cpp += this_line
            if ";" in this_line:
                break

        # common ep types
        ep_types = ["Array1D_int ",
                    "Array1D_string ",
                    "Array1D_bool ",
                    "Real64 ",
                    "int ",
                    "bool ",
                    "std::string ",
                    "ObjexxFCL::gio::Fmt "]

        # get common ep types
        chars = list(raw_cpp)
        comment_char_idxs = []

        for idx, ch in enumerate(chars):
            if ch == "\"":
                comment_char_idxs.append(idx)

        comments = []
        for idx in range(0, len(comment_char_idxs), 2):
            comments.append("".join(chars[comment_char_idxs[idx]: comment_char_idxs[idx + 1] + 1]))

        basic_type = False

        if "<" not in raw_cpp:
            basic_type = True
        else:
            for c in comments:
                if "<" in c:
                    basic_type = True

        if raw_cpp.count(" ") == 1:
            cpp_type = raw_cpp.split(" ")[0]
        elif basic_type:
            for idx, ep_type in enumerate(ep_types):
                if ep_type in raw_cpp:
                    cpp_type = ep_type.strip()
                    break
        else:
            # try to determine other types
            try:
                num_open_brackets = 0
                num_closed_brakets = 0
                start_found = False
                for ch in raw_cpp:
                    cpp_type += ch
                    if ch == "<":
                        start_found = True
                        num_open_brackets += 1
                    elif ch == ">":
                        num_closed_brakets += 1

                    if num_open_brackets - num_closed_brakets == 0 and start_found:
                        break
            except:
                logging.warning("{} : type not found".format(raw_cpp))
                cpp_type = ''

        # other data for convenience
        if "static" in raw_cpp:
            is_static = True
        if "const" in raw_cpp:
            is_const = True

        # attempt to determine initial value
        if "=" in raw_cpp:
            init_val = raw_cpp.split("=")[1].strip().replace(";", "")
        elif "(" in raw_cpp:
            num_open_brackets = 0
            num_closed_brakets = 0
            start_found = False
            for ch in raw_cpp:
                if ch == "(":
                    start_found = True
                    num_open_brackets += 1
                    continue
                elif ch == ")":
                    num_closed_brakets += 1
                    if num_open_brackets - num_closed_brakets == 0:
                        break
                    else:
                        continue

                if start_found:
                    init_val += ch
                else:
                    continue

        # test initial value
        if init_val == "true":
            init_val = True
        elif init_val == "false":
            init_val = False
        elif "," in init_val \
                or "{" in init_val \
                or "*" in init_val \
                or "/" in init_val \
                or "+" in init_val \
                or "-" in init_val \
                or "\"" in init_val:
            pass
        elif "" == init_val:
            pass
        else:
            try:
                init_val = int(init_val)
            except ValueError:
                try:
                    init_val = float(init_val)
                except:
                    pass
            except:
                pass

        return {'type': cpp_type,
                'initial-value': init_val,
                'is-const': is_const,
                'is-static': is_static,
                'raw-cpp': raw_cpp}

    def process_single_file(self, file_idx):

        # if no vars to process, skip
        if "vars" in self.d_files[file_idx]:

            # load cpp file into memory
            cpp_lines = []
            with open(self.d_files[file_idx]['path'], 'r') as f:
                # add empty line at beginning so line no's match the index
                cpp_lines.append('')
                for line in f:
                    cpp_lines.append(line)

            # get raw cpp line for each var
            for var_idx, var in enumerate(self.d_files[file_idx]['vars']):
                line_no = self.d_files[file_idx]['vars'][var_idx]['line-no']
                d_cpp = self.get_cpp_data(cpp_lines, line_no)

                # pull in line data
                self.d_files[file_idx]['vars'][var_idx] = {**self.d_files[file_idx]['vars'][var_idx], **d_cpp}

    def process(self):

        for file_idx, d_file in enumerate(self.d_files):
            try:
                logging.info("{} : started".format(d_file['path']))
                self.process_single_file(file_idx)
                logging.info("{} : completed".format(d_file['path']))
            except:
                logging.info("{} : failed".format(d_file['path']))
        with open(self.output_dir, 'w+') as f:
            f.write(json.dumps(self.d_files, sort_keys=True, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', dest="source_dir",
                        help="path to the EnergyPlus /src/EnergyPlus dir")
    parser.add_argument('-c', dest='preprocess_csv')
    parser.add_argument('-o', dest="output_file",
                        help="(optional) path to the output directory. If path not given, output files will"
                             "be written in place.")
    parser.add_argument('-l', dest="list_file",
                        help="(optional) path to list file with .cc file names to process. If list file not given, "
                             "all .cc files in /src/EnergyPlus will be processed.")

    results = parser.parse_args()

    if results.source_dir is None:
        raise SystemExit("source_dir '-s' argument required")
    else:
        P = TypeInitFinder(source_dir=results.source_dir,
                           preprocess_csv=results.preprocess_csv,
                           list_file=results.list_file,
                           output_dir=results.output_file)
        P.process()

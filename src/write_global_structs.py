import argparse
import json
import logging


class GlobalWriter(object):
    def __init__(self, preprocess_json, output_dir=None):

        logging.basicConfig(filename='write_global.log',
                            filemode='w',
                            format='%(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        with open(preprocess_json, 'r') as f:
            self.d_files = json.load(f)

        # sort
        self.d_files = sorted(self.d_files, key=lambda i: (i["file-name"]))

        for idx, d in enumerate(self.d_files):
            if "vars" in d:
                self.d_files[idx]["vars"] = sorted(d['vars'], key=lambda i: (i["type"], i["name"]))

        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = "globals.hpp"

    @staticmethod
    def write_clear_var(var):
        var_str = "    "

        if "std::vector" in var["type"]:
            var_str += "{}.clear();\n".format(var["name"], var["initial-value"])
        elif var["type"] in ["int", "Real64", "std::string"]:
            if var["initial-value"] == "":
                var_str += "{} = {};\n".format(var["name"], "")
            else:
                var_str += "{} = {};\n".format(var["name"], var["initial-value"])
        elif var["type"] == "bool":
            if var["initial-value"]:
                var_str += "{} = true;\n".format(var["name"])
            else:
                var_str += "{} = false;\n".format(var["name"])
        elif "Array" in var["type"]:
            var_str += "{}.deallocate();\n".format(var["name"], var["initial-value"])
        else:
            var_str += "{} = {};\n".format(var["name"], var["initial-value"])

        return var_str

    def write_clear_state(self, d_file):
        clear_str = "void {}Globals::clear_state()\n".format(d_file["file-name"].split(".cc")[0])
        final_str = "    {}Globals::clear_state();\n".format(d_file["file-name"].split(".cc")[0])
        clear_str += "{\n"
        all_vars_const = True
        for var in d_file["vars"]:
            if not var["is-const"]:
                all_vars_const = False
                clear_str += self.write_clear_var(var)

        clear_str += "};\n\n"

        if all_vars_const:
            clear_str = ""
            final_str = ""

        return clear_str, final_str

    @staticmethod
    def write_struct_var(var):
        var_str = ''

        key = "type"
        if key in var:
            var_str += "    {}".format(var[key])
        else:
            return "", True

        key = "is-const"
        if key in var:
            if var[key] is True:
                var_str += " const"
            elif var[key] is False:
                pass
        else:
            return "", True

        key = "name"
        if key in var:
            var_str += " {}".format(var[key])
        else:
            return "", True

        key = "initial-value"
        if (key in var) and (var[key] is not ""):
            if var[key] is True:
                var_str += "({});".format("true")
            elif var[key] is False:
                var_str += "({});".format("false")
            else:
                var_str += "({});".format(var[key])
        else:
            var_str += ";"

        var_str += "\n"

        return var_str, False

    def write_to_struct(self, d_file):

        # write to temp string
        struct_str = ''
        struct_str += "struct {}Globals\n".format(d_file["file-name"].split(".cc")[0])
        struct_str += "{\n"
        all_vars_const = True
        for var in d_file['vars']:
            errors_found = False
            var_str = ""
            if not var["is-const"]:
                all_vars_const = False
                var_str, errors_found = self.write_struct_var(var)
            if errors_found:
                logging.warning("{} : error writing variable".format(json.dumps(var)))
                break
            else:
                struct_str += var_str

        struct_str += "\n    void clear_state();\n"
        struct_str += "};\n\n"

        if all_vars_const:
            struct_str = ""

        return struct_str

    def process(self):
        with open(self.output_dir + "globals.hpp", 'w+') as f_hpp, open(self.output_dir + "globals.cpp", 'w+') as f_cpp:
            final_clear_str = "void EPGlobals::clear_state()\n{\n"
            for idx, d_file in enumerate(self.d_files):
                if "vars" not in d_file:
                    pass
                elif len(d_file["vars"]) > 0:
                    try:
                        logging.info("{} : starting hpp".format(json.dumps(d_file["file-name"])))
                        hpp_str = self.write_to_struct(d_file)
                        f_hpp.write(hpp_str)
                        logging.info("{} : complete hpp".format(json.dumps(d_file["file-name"])))
                    except:
                        logging.warning("{} : error writing hpp file".format(json.dumps(d_file["file-name"])))

                    try:
                        logging.info("{} : starting cpp".format(json.dumps(d_file["file-name"])))
                        cpp_str, clear_str = self.write_clear_state(d_file)
                        final_clear_str += clear_str
                        f_cpp.write(cpp_str)
                        logging.info("{} : complete cpp".format(json.dumps(d_file["file-name"])))
                    except:
                        logging.warning("{} : error writing cpp file".format(json.dumps(d_file["file-name"])))

            final_clear_str += "};\n"
            f_cpp.write(final_clear_str)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', dest='preprocess_json', help="path to preprocessed json file")

    parser.add_argument('-o', dest="output_file",
                        help="(optional) path to the output directory. If path not given, output files will"
                             "be written in place.")

    results = parser.parse_args()

    if results.preprocess_json is None:
        raise SystemExit("preprocess_json '-c' argument required")
    else:
        P = GlobalWriter(preprocess_json=results.preprocess_json, output_dir=results.output_file)
        P.process()

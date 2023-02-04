import sys
import os
import argparse

from engines import VMCompilationEngine, XMLCompilationEngine

parser = argparse.ArgumentParser()
parser.add_argument("-x", "--xml", action="store_true", help="output xml")
parser.add_argument("path", help="file or directory to be compiled")
args = parser.parse_args()
path, xml = args.path, args.xml

compilation_engine = XMLCompilationEngine() if xml else VMCompilationEngine()

dirname, basename = os.path.split(path)
base_no_ext, ext = os.path.splitext(basename)

# compile a directory containing .jack files
if os.path.isdir(path):
    os.chdir(path)
    error_code = 0
    files = []
    # scan dir for .jack files
    for entry in os.scandir():
        class_name, ext = os.path.splitext(entry.name)
        if os.path.isfile(entry.name) and ext == ".jack":
            files.append(class_name)
    # compile each .jack file
    for i, class_name in enumerate(files):
        success = compilation_engine.run(class_name)
        if not success:
            error_code = 1
            quit = ""
            if i < len(files)-1:
                while quit != "y":
                    quit = input("Continue compiling directory? (y/n)\n")
                    if quit == "n":
                        sys.exit(1)
                    elif quit != "y":
                        print("Invalid response.")
    sys.exit(error_code)
# compile an individual .jack file
elif os.path.isfile(path) and ext == ".jack":
    if dirname:
        os.chdir(dirname)
    success = compilation_engine.run(base_no_ext)
    if not success:
        sys.exit(1)
else:
    print(
            "Error: The provided path does not match "
            "any directory or .jack file."
            )
    sys.exit(1)

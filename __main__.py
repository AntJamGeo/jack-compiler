import sys
import os
import argparse

from comptools import CompilationEngineVM, CompilationEngineXML

def compile(basename, base_no_ext):
    with compilation_engine(basename) as engine:
        success, output = engine.run()
    if success:
        print(f"File '{basename}' compiled to '{output}' successfully!")
    else:
        os.remove(output)
        sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("-x", "--xml", action="store_true", help="output xml")
parser.add_argument("path", help="file or directory to be compiled")
args = parser.parse_args()
path, xml = args.path, args.xml

compilation_engine = CompilationEngineXML if xml else CompilationEngineVM

dirname, basename = os.path.split(path)
base_no_ext, ext = os.path.splitext(basename)

if os.path.isdir(path):
    os.chdir(path)
    files = []
    for entry in os.scandir():
        name_no_ext, ext = os.path.splitext(entry.name)
        if os.path.isfile(entry.name) and ext == ".jack":
            files.append((entry.name, name_no_ext))
    for basename, base_no_ext in files:
        compile(basename, base_no_ext)
elif os.path.isfile(path) and ext == ".jack":
    if dirname:
        os.chdir(dirname)
    compile(basename, base_no_ext)
else:
    print(
            "Error: The provided path does not match "
            "any directory or .jack file."
            )
    sys.exit(1)

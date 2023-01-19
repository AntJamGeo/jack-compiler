import sys
import os

from comptools import CompilationEngine

def compile(basename, base_no_ext):
    with CompilationEngine(basename) as engine:
        success = engine.run()
    if success:
        print(f"File '{basename}' compiled successfully!")
    else:
        os.remove(base_no_ext + ".xml")
        sys.exit(1)

path = sys.argv[1]
dirname, basename = os.path.split(path)
base_no_ext, ext = os.path.splitext(basename)

if os.path.isdir(path):
    os.chdir(path)
    files = []
    for entry in os.scandir():
        name_no_ext, ext = os.path.splitext(entry.name)
        if os.path.isfile(entry.name) and ext == ".jack":
            files.append((entry.name, name_no_ext))
    for basename, name_no_ext in files:
        compile(basename, name_no_ext)
elif os.path.isfile(path) and ext == ".jack":
    if dirname:
        os.chdir(dirname)
    compile(basename)
else:
    print(
            "Error: The provided path does not match "
            "any directory or .jack file."
            )
    sys.exit(1)

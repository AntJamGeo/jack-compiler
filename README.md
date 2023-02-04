# Jack Compiler
The Jack Compiler is used in the first stage of a two-stage compilation process of a program written in an object-based programming language.

This translator takes .jack files and produces .vm files, ready for the second stage of compilation using the [Hack Virtual Machine Translator](https://github.com/AntJamGeo/hack-vm-translator), where they get combined into a single .asm file to be ran on the Hack computer, a simple computer that is built in the first part of the nand2tetris course (references below).

## Usage

The compiler requires a .jack file or a directory containing .jack files to be provided to it in order to run. For each .jack file encountered, a single .vm file will be produced; in the case of single file translation, this file will appear in the same directory as the .jack file, while for a directory, it will appear within the given directory.

To use, clone this repository and run `python3 <path to compiler directory> <path to target .jack file or directory>`. For example, if the current working directory is the jack-compiler directory and we add
* `example.jack` to the directory, running `python3 compiler example.jack` will produce `example.vm` in the jack-compiler directory;
* a directory called `example` to the directory, running `python3 compiler example` will produce one .vm file for each .jack file in the `example` directory and place those files in the `example` directory.

Optionally add the `-x` flag (e.g. `python3 compiler -x example`) to output .xml files instead of .vm files. These are used to clearly see each token in XML format in a .jack file.

## References
* nand2tetris Website: https://www.nand2tetris.org/
* Part 1 of the Course (Hardware): https://www.coursera.org/learn/build-a-computer
* Part 2 of the Course (Software): https://www.coursera.org/learn/nand2tetris2

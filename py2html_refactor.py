import os
import re
import sys
import importlib.util
from pathlib import Path
import argparse
import FWCore.ParameterSet.Config as cms
import FWCore.ParameterSet.SequenceTypes as cmsSequenceTypes
import HeterogeneousCore.CUDACore.SwitchProducerCUDA as switchProducerCUDA


class Visitor:
    def __init__(self, out, process, prefix):
        self.out = out
        self.process = process
        self.prefix = prefix
        self.githubSearch = (
            "https://github.com/search?q=repo%3Acms-sw%2Fcmssw%20{cpp_type}&type=code"
        )

    def enter(self, value):
        element_type = type(value)
        label = self.get_label(value)

        if element_type is cms.Sequence:
            self._write_sequence(label)
        elif element_type is cms.Task:
            self._write_task(label)
        else:
            self._write_element_type(value)

    def leave(self, value):
        self._write_output(value)

    def get_label(self, value):
        if getattr(value, "hasLabel_", None):
            if value.hasLabel_():
                # I had to revert using label_ because some EPProducer have a
                # valid label configuration parameter that is hiding the
                # original label method and that is non callable.
                return value.label_()
        else:
            return "--No label found--"

    def _write_sequence(self, label):
        self.out.write(f"<li class=sequence>Sequence {label}</li><ol>\n")

    def _write_task(self, label):
        self.out.write(f"<li class=task>Task {label}</li><ol>\n")

    def _write_element_type(self, value):
        is_ignored = ""
        is_negation = ""
        element_map = {
            cms.EDAnalyzer: "EDAnalyzer",
            cms.EDProducer: "EDProducer",
            cms.EDFilter: "EDFilter",
            cms.SwitchProducer: "SwitchProducer",
            cmsSequenceTypes._SequenceIgnore: "SequenceIgnore",
            cmsSequenceTypes._SequenceNegation: "SequenceNegation",
            cmsSequenceTypes.SequencePlaceholder: "SequencePlaceholder",
            cmsSequenceTypes.TaskPlaceholder: "TaskPlaceholder",
            switchProducerCUDA.SwitchProducerCUDA: "SwitchProducerCUDA",
        }
        element_type = element_map.get(type(value))
        cpp_type = None
        if type(value) is cmsSequenceTypes._SequenceIgnore:
            is_ignored = " [-] "
            cpp_type = value._operand.type_()
        elif type(value) is cmsSequenceTypes._SequenceNegation:
            is_negation = " [!] "
        elif (
            type(value) is cmsSequenceTypes.TaskPlaceholder
            or type(value) is cmsSequenceTypes.SequencePlaceholder
        ):
            pass
        elif type(value) is switchProducerCUDA.SwitchProducerCUDA:
            cpp_type = element_type
        else:
            cpp_type = value.type_()
        githubSearch = self.githubSearch.format(cpp_type=cpp_type)
        self.out.write(
            f'<li class="{element_type}">{is_ignored} {is_negation} {cpp_type} <a href={githubSearch} target="_blank" class="github-link"> [+] </a>'
        )
        if (
            type(value) is not cmsSequenceTypes._SequenceIgnore
            and type(value) is not cmsSequenceTypes._SequenceNegation
        ):
            self._dump_producer_or_filter(value)

    def _dump_producer_or_filter(self, value):
        tmpout = open(
            os.path.join(self.prefix, "html/", self.get_label(value) + ".html"), "w"
        )
        tmpout.write(preamble())
        tmpout.write("<pre>\n")
        lines = []
        gg = value.dumpPython()
        lines = gg.split("\n")
        self.printAndExpandRefs(lines, tmpout, "")

    def _fake(self):
        return "Not_Available"

    def _write_output(self, value):
        label = self.get_label(value)

        if (
            type(value) is cmsSequenceTypes._SequenceIgnore
            or type(value) is cmsSequenceTypes._SequenceNegation
        ):
            pass
        elif type(value) is cms.Sequence or type(value) is cms.Task:
            self.out.write("</ol>\n")
        else:
            self.out.write(
                f'<span style="color:#000000"><a href={label}.html> {label} </a></span>'
            )
            self.out.write("</li>\n")

    def printAndExpandRefs(self, lines, tmpout, indent):
        cutAtColumn = 978
        for line in lines:
            refs = re.search(r"refToPSet_\s+=\s+.*'(.*?)'", line)
            blocks = len(line) / cutAtColumn + 1
            for i in range(0, int(blocks)):
                tmpout.write(
                    "%s%s" % (indent, line[i * cutAtColumn : (i + 1) * cutAtColumn])
                )
                if blocks > 1 and not (i == blocks):
                    tmpout.write("\\ \n")
                else:
                    tmpout.write("\n")
            if refs:
                indent = "  ".join((indent, ""))
                tmpout.write(
                    "%s----------------------------------------------------------\n"
                    % indent
                )
                self.printAndExpandRefs(
                    getattr(self.process, refs.group(1)).dumpPython().split("\n"),
                    tmpout,
                    indent,
                )
                tmpout.write(
                    "%s----------------------------------------------------------\n"
                    % indent
                )
        indent = indent[:-2]


def dumpESProducer(value, out, prefix):
    type_ = getattr(value, "type_", "Not Available")
    filename_ = getattr(value, "_filename", "Not Available")
    lbl_ = getattr(value, "label_", "Not Available")
    link = ""
    githubSearch = "https://github.com/search?q=repo%3Acms-sw%2Fcmssw%20{cpp_type}&type=code".format(
        cpp_type=type_()
    )
    link = "<a href={} target='_blank' class='github-link'> {} </a>\n".format(
        githubSearch, type_()
    )
    out.write(
        "<ol><li>"
        + link
        + ", label <a href="
        + lbl_()
        + ".html>"
        + lbl_()
        + "</a>, defined in "
        + filename_
        + "</li></ol>\n"
    )
    tmpout = open(os.path.join(prefix, "html", lbl_() + ".html"), "w")
    tmpout.write(preamble())
    tmpout.write("<pre>\n")
    gg = value.dumpPython()
    for line in gg.split("\n"):
        tmpout.write(line)
    tmpout.write("<pre>\n")
    tmpout.write("</body>\n</html>\n")
    tmpout.close()


def check_environment():
    if not os.getenv("CMSSW_RELEASE_BASE"):
        print("CMSSW environment not set. Exiting.")
        sys.exit(1)


def preamble() -> str:
    return """
<html>
 <head>
  <title>Config Browser</title>
  <style type="text/css">
  ol {
   font-family: Arial;
   font-size: 10pt;
   padding-left: 25px;
  }
  .sequence {
   font-weight: bold;
  }
  .task {
   font-weight: bold;
  }
  li.Path       {font-style:bold;   color: #03C;}
  li.Task       {font-style:bold;   color: #3465A4;}
  li.sequence   {font-style:bold;   color: #09F;}
  li.task       {font-style:bold;   color: #FF6666;}
  li.EDProducer {font-style:italic; color: #a80000;}
  li.EDFilter   {font-style:bold; color: #F90;}
  li.EDAnalyzer {font-style:italic; color: #360;}
  li.SwitchProducer {font-style:italic; color: #4e9a06;}
  li.SequenceIgnore {font-style:bold; color: #a800a8;}
  li.SequenceNegation {font-style:bold; color: #a800a8;}
  .github-link {
      color: #ce5c00; /* Custom blue color */
      text-decoration: none; /* Remove underline if desired */
  }

  .github-link:hover {
      color: #4e9a06; /* Change color on hover */
      text-decoration: underline; /* Optional hover effect */
  }

</style>
 </head>

 <body>
"""


def end_document() -> str:
    return "</body>\n</html>\n"


def load_module_from_file(filepath: str, module_name: str):
    fp = Path(filepath)
    spec = importlib.util.spec_from_file_location(module_name, fp)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main(args):
    check_environment()

    try:
        config_module = load_module_from_file(args.input_cfg, "config_module")
        process = getattr(config_module, "process", None)
    except Exception:
        print("Failed to import configuration module.")
        sys.exit(1)

    if not os.path.exists(os.path.join(args.output, "html")):
        os.makedirs(os.path.join(args.output, "html"))

    with open(os.path.join(args.output, "html", "index.html"), "w") as out:
        out.write(preamble())

        # Create a small TOC pointing to all the paths defined inside the supplied
        # python configuration.
        out.write("<h1>Link into Paths</h1><ol>\n")
        for k in process.paths.keys():
            out.write('<li><a href="#%s">Path %s</a></li>\n' % (k, k))
        out.write("</ol>\n\n")

        visitor = Visitor(out, process, args.output)

        # Dump all the paths and their contents
        out.write("<ol>\n\n")
        for path_name, path in process.paths.items():
            out.write(f'<li id="{path_name}" class="Path">Path {path_name}</li>\n<ol>')
            path.visit(visitor)
            out.write("</ol>")
        out.write("</ol>\n\n")

        out.write("<h1>ES Producers</h1>\n")
        for k in process.es_producers_().keys():
            out.write("<H2>ESProducer %s</H2>\n" % k)
            dumpESProducer(process.es_producers[k], out, args.output)

        out.write(end_document())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input_cfg", required=True, type=str, help="Input configuration file"
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=str,
        help="Output directory for HTML files",
    )
    args = parser.parse_args()
    main(args)

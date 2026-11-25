# Licences of the shipped tools

The files in this repository (launcher, Makefile templates, examples, docs) are under the MIT licence in
`../LICENSE`.

Each tool in the release bundle keeps its own licence. The full table is in [../docs/TOOLS.md](../docs/TOOLS.md).
Inside the release bundle, the licence texts are here:

| Tool(s) | Where the licence text is |
|---|---|
| MSYS2 packages (Verilator, GCC, Icarus, Yosys, Python, z3, make, perl, lcov, lz4, vim, bash, ...) | `ucrt64\share\licenses\<package>\` and `usr\share\licenses\<package>\` (where the package ships one) |
| UVM (Apache-2.0) | `opt\uvm\LICENSE.txt`, `opt\uvm\NOTICE.txt` |
| gvim (Vim licence) | `opt\gvim\vim\vim92\LICENSE.txt` (as shipped in the official ZIP) |
| Graphviz (EPL-2.0) | **to be added**: the official Windows ZIP has no licence file. The text is at <https://graphviz.org/license/> |
| Surfer (EUPL-1.2) | **to be added**: the official Windows ZIP has no licence file. The text is at <https://eupl.eu/1.2/en/> |

**Open item before a full release:** collect one folder per tool with its licence text and source link, and add the
Graphviz and Surfer licence texts. The source code of the GPL tools is available from the MSYS2 project (each package's source)
and the upstream links in TOOLS.md.

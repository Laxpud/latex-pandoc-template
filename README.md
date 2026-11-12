# LaTeX Pandoc Manuscript Template

- 🌐 **[中文 README](<docs/README.cn.md>)**: Chinese guide.
- 🛠️ **[Technical Notes](<docs/technical-stack.md>)**: Conversion internals, styles, and troubleshooting.
- 🗺️ **[Documentation Index](<docs/index.md>)** · ✅ **[Project TODO](<TODO.md>)**

A minimal LaTeX manuscript template and a reusable Pandoc-to-Word converter. Copy the [template directory](<template/>) for each new paper; keep the converter in this repository and call it from your manuscript directory. Authors and affiliations, abstract, keywords, figures, tables, equations, citations, and cross references are retained without requiring a journal-specific class.

This is a drafting and review workflow, not a final journal submission template. If it helps, stars, issues, and contributions are welcome.

## Repository Layout

```text
template/                    Copy this directory to start a paper
  temp.tex                   Manuscript source
  reference.bib              Bibliography
  gbt7714.bst                PDF bibliography style
  fig/                       Example figures
  .vscode/settings.json     LaTeX Workshop recipes
  .gitignore                 Generated-file exclusions
  LICENSE                    License notice for the copied template
src/lpt_docx/                Conversion modules
  resources/                 Lua filter, CSL, and Word style template
bin/                        Repository launchers
  lpt-docx                   Bash entry point; supports symbolic links
  lpt-docx.ps1               PowerShell entry point
tests/                      Existing conversion tests
```

The copied template has everything needed for PDF compilation. Python code, the Lua filter, and Word conversion resources stay with the tool; they do not need to be copied into each paper.

## Requirements

- TeX Live with `xelatex` and `bibtex` for PDF compilation: [TeX Live](https://www.tug.org/texlive/acquire.html).
- Pandoc for Word conversion: [Installing Pandoc](https://pandoc.org/installing.html).
- uv for the converter's Python environment: [Installing uv](https://docs.astral.sh/uv/getting-started/installation/).
- Bash on Linux, or PowerShell on Windows for the corresponding repository launcher.

The existing CI targets Windows and Ubuntu with Pandoc 3.8.3, Lua 5.4, uv 0.11.32, and Python 3.10. Python dependencies are `lxml>=5.3.0` and `PyMuPDF>=1.24.0`; uv prepares them automatically. PDF compilation uses the local TeX Live installation.

## Quick Start

### 1. Get the repository

```console
git clone https://github.com/Laxpud/latex-pandoc-template.git
cd latex-pandoc-template
```

Without Git, download and extract the repository using `Code -> Download ZIP` on [GitHub](https://github.com/Laxpud/latex-pandoc-template).

### 2. Make the converter available

On Linux, link the [Bash launcher](<bin/lpt-docx>) into your personal bin directory from the repository root:

```bash
mkdir -p "$HOME/bin"
ln -s "$(pwd)/bin/lpt-docx" "$HOME/bin/lpt-docx"
export PATH="$HOME/bin:$PATH"
```

Use any personal bin directory already on your `PATH`. Add the `PATH` setting to your shell configuration if needed. The command intentionally does not overwrite an existing link or executable. Keep the repository available while using this link; the launcher follows absolute or relative symlink chains, locates the tool environment, and leaves your manuscript working directory unchanged.

On Windows, or if you prefer an installed command on either platform:

```console
uv tool install .
```

If uv's executable directory is not on `PATH`, run `uv tool update-shell` and open a new terminal. The installed command and repository launchers use the same Python package.

### 3. Copy the template for a new paper

Linux, from the repository root:

```bash
cp -a template ../my-paper
cd ../my-paper
```

Windows PowerShell:

```powershell
Copy-Item -Recurse template ..\my-paper
Set-Location ..\my-paper
```

Choose a new destination directory, then replace the example content. Hidden editor settings and generated-file exclusions are copied too. You can rename the paper directory freely; if you also rename the main TeX file, pass its new name to the converter.

### 4. Compile PDF and convert to Word

Run these commands inside your copied paper directory:

```console
xelatex -interaction=nonstopmode temp.tex
bibtex temp
xelatex -interaction=nonstopmode temp.tex
xelatex -interaction=nonstopmode temp.tex
lpt-docx
```

The PDF and Word review draft are created beside the main TeX file. For a renamed manuscript:

```console
lpt-docx manuscript.tex
lpt-docx manuscript.tex --output manuscript-review.docx
```

## Files To Edit

In your copied paper directory, edit the equivalents of:

- [temp.tex](<template/temp.tex>): title, authors, numbered affiliations, corresponding-author email, abstract, keywords, and body.
- [reference.bib](<template/reference.bib>): bibliography entries.
- [fig/](<template/fig/>): figures to keep with the manuscript.

The [BibTeX style](<template/gbt7714.bst>) stays with the paper for PDF compilation. The converter's [CSL](<src/lpt_docx/resources/gbt7714.csl>) and [Word style template](<src/lpt_docx/resources/reference.docx>) stay in the tool repository.

### Optional VS Code Workflow

Install [VS Code](https://code.visualstudio.com/download) and [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop), then open the copied paper directory, not the converter repository:

```console
code .
```

The copied [editor settings](<template/.vscode/settings.json>) provide `latexmk` and `xelatex -> bibtex -> xelatex*2` recipes. Automatic builds are disabled; use `LaTeX Workshop: Build with recipe` when needed. The recipes use the active document name, so renaming the main file does not require editing them.

## Conversion Options

With no arguments, `lpt-docx` reads your copy of [temp.tex](<template/temp.tex>) in the current paper directory. The project root defaults to the input directory; output uses the input basename with a `.docx` suffix; bibliography defaults to the paper's [reference.bib](<template/reference.bib>); cache is written inside the paper's `.pandoc-cache/` directory. The converter takes its default Lua filter, CSL, and Word styles from its own package, not from the paper or the invocation directory.

All existing options remain available:

```console
lpt-docx --help
lpt-docx paper.tex --bibliography references.bib --output review.docx
lpt-docx tex/paper.tex --project-root . --resource-dir extra-assets
```

Relative command-line paths use the invocation directory. TeX image paths use the manuscript project root and `\graphicspath`. `--bibliography` and `--resource-dir` may be repeated; `--input`, `--csl`, `--reference-doc`, `--cache-dir`, and `--image-dpi` are also supported.

Without installing or linking a command, call a repository launcher by absolute path from a paper directory:

```bash
/path/to/latex-pandoc-template/bin/lpt-docx manuscript.tex
```

```powershell
& "C:\tools\latex-pandoc-template\bin\lpt-docx.ps1" manuscript.tex
```

## Writing Tips

- Start from the supplied template and replace its example content incrementally; arbitrary journal templates may use unsupported commands.
- Keep author superscripts consistent with the numbered affiliations. When changing the email, update both the `mailto:` target and visible text; see [Front Matter](<docs/technical-stack.md#front-matter>).
- Keep the explicit page break between keywords and the introduction if the body should start on a new page.
- Use standard `\section`, `\subsection`, `\subsubsection`, `figure`, `table`, `equation`, `\label`, `\ref`, and `\cite` structures; prefer `booktabs` tables.
- Keep figures inside the paper. PDF figures are rendered to cached PNGs for Word; PNG and JPG figures can be used directly.
- Avoid journal-specific columns, headers, footers, and complex title pages during drafting. Migrate to the journal template when the content is ready.

## Maintenance And Migration

The previous root-level manuscript files now live in the template directory. Conversion modules and resources now live entirely under the [Python package](<src/lpt_docx/>). Old root-level conversion wrappers and the legacy script wrapper have been replaced by the bin launchers; existing installed `lpt-docx` commands and CLI arguments remain supported. Reinstall or upgrade an existing non-editable tool installation to use the refactored version.

For development, run from the repository root:

```console
uv sync
uv run python -m unittest discover -s tests -v
uv build
```

To repair the bundled Word style template after replacing it, run from the repository root:

```console
uv run python -m lpt_docx.namespace_reference_docx_styles src/lpt_docx/resources/reference.docx
```

Generated documents, LaTeX auxiliary files, Python environments, and caches are not source assets. The [template ignore rules](<template/.gitignore>) travel with each copied paper; original PDF figures remain versionable. See [Technical Notes](<docs/technical-stack.md>) for style maintenance and troubleshooting.

## Contributing

Reports of real conversion problems, documentation improvements, and contributions to figures, tables, references, or Word styles are welcome. Keep generated artifacts out of commits and describe non-trivial changes and validation in the commit body.

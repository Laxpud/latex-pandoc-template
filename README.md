# LaTeX Pandoc Manuscript Template

- 🌐 **[中文 README](docs/README.cn.md)**: Chinese guide for this template.
- 🗺️ **[Technical Docs Index](docs/index.md)**: Technical notes, maintenance docs, and archived plans.
- 🛠️ **[Technical Stack and Implementation Notes](docs/technical-stack.md)**: File responsibilities, conversion pipeline, scripts, and maintenance notes.
- ✅ **[Project TODO](TODO.md)**: Active documentation and conversion work.
- 🤝 **[Contributing](#contributing)**: Report issues, share use cases, or help improve the template.

This is a minimal LaTeX template for drafting academic manuscripts. It keeps common paper structures such as title, authors, abstract, keywords, sections, figures, tables, equations, cross references, and references, while avoiding complex journal-specific layout commands so the manuscript can be converted to a Word review draft with Pandoc.

If this template helps you avoid some LaTeX-to-Word conversion pain, please consider starring the repository. Issues, usage stories, and contributions are also welcome.

## What This Is For

- Drafting a manuscript in `temp.tex`.
- Compiling a PDF with XeLaTeX to check equations, figures, and references.
- Converting the manuscript to Word for advisor, collaborator, or internal review.
- Moving the finished draft to a target journal template later.

## Environment

Required tools:

- TeX Live, with `xelatex` and `bibtex` available. Official download page: [TeX Live](https://www.tug.org/texlive/acquire.html).
- Pandoc. Official download page: [Installing pandoc](https://pandoc.org/installing.html).
- uv, used to create the Python environment and run the conversion scripts. Official installation page: [Installing uv](https://docs.astral.sh/uv/getting-started/installation/).
- PowerShell on Windows, or Bash on Linux. Windows includes PowerShell, and common Linux distributions include Bash.

Optional editor setup:

- VS Code. Official download page: [Download Visual Studio Code](https://code.visualstudio.com/download).
- LaTeX Workshop extension. Install it from the VS Code extension marketplace, or see the extension page: [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop).
- Git. If you do not want to install Git, you can download the repository as a ZIP file from GitHub. Official download page: [Git Downloads](https://git-scm.com/downloads/).

This repository already includes LaTeX Workshop recipes in `.vscode/settings.json`:

- `latexmk`: uses `latexmk -xelatex` to handle multi-pass compilation automatically.
- `xelatex -> bibtex -> xelatex*2`: explicitly runs the full bibliography compilation sequence.

Automatic LaTeX Workshop builds are disabled with `latex-workshop.latex.autoBuild.run = never`, so the project does not recompile repeatedly whenever files are opened or saved. To build manually, run `LaTeX Workshop: Build with recipe` from the VS Code command palette and choose a recipe.

The Word conversion pipeline is tested automatically on Windows and Ubuntu with:

- Pandoc 3.8.3, Lua 5.4.
- uv 0.11.32 and Python 3.10.
- Python dependencies: `lxml>=5.3.0` and `PyMuPDF>=1.24.0`.

PDF compilation remains based on XeLaTeX and BibTeX from TeX Live.

For detailed file descriptions, conversion internals, and maintenance notes, see [Technical Stack and Implementation Notes](docs/technical-stack.md).

## Quick Start

The steps below assume a fresh local directory. Commands that differ between Windows and Linux are shown separately.

1. Get the project files.

   If Git is installed, `git clone` is recommended:

   ```powershell
   git clone https://github.com/Laxpud/latex-pandoc-template.git
   cd latex-pandoc-template
   ```

   If Git is not installed, download the project manually:

   1. Open <https://github.com/Laxpud/latex-pandoc-template>.
   2. Click `Code`.
   3. Choose `Download ZIP`.
   4. Extract the ZIP file.
   5. In a terminal, enter the extracted `latex-pandoc-template` folder.

2. Open the project folder in VS Code:

   ```powershell
   code .
   ```

   If the `code` command is unavailable, open VS Code first, then choose `File -> Open Folder...` and select the `latex-pandoc-template` folder.

3. Install or confirm the LaTeX Workshop extension in VS Code.

   The repository already provides `.vscode/settings.json`, so LaTeX Workshop will load the project recipes after the folder is opened.

4. Prepare Python dependencies:

   ```powershell
   uv sync
   ```

   This creates `.venv/` and installs the Python dependencies used by the conversion scripts.

5. Open `temp.tex` and compile the PDF first.

   In the VS Code command palette, run `LaTeX Workshop: Build with recipe`, then choose `latexmk` or `xelatex -> bibtex -> xelatex*2`.

   A successful build produces `temp.pdf`. If VS Code does not display it automatically, open `temp.pdf` from the file list.

6. Convert the manuscript to a Word review draft.

   On Windows:

   ```powershell
   .\convert-docx.ps1
   ```

   On Linux:

   ```bash
   ./convert-docx.sh
   ```

   A successful conversion produces `temp.docx`.

7. Start replacing the example content.

   Focus first on `temp.tex`, `reference.bib`, and `fig/`. It is best to keep the example section, figure, table, equation, and reference structure at the beginning, then gradually replace it with your own paper content.

## Files To Edit First

If you are new to LaTeX, you usually only need to focus on:

- `temp.tex`: the manuscript source. Edit the title, authors, abstract, keywords, sections, figures, tables, equations, and citations here.
- `reference.bib`: the BibTeX reference database. Add journal papers, books, web pages, and other references here.
- `fig/`: the figure directory. Put the PNG, JPG, or PDF images used by the manuscript here.

Start by replacing the examples in `temp.tex`. Avoid changing the preamble or conversion scripts at the beginning. For detailed file responsibilities, see [Technical Stack and Implementation Notes](docs/technical-stack.md).

## Files To Notice But Usually Not Edit

These files usually do not need to be modified while drafting:

- `gbt7714.bst` and `gbt7714.csl`: reference styles for PDF and Word output.
- `reference.docx`: Word style template. Edit it only when you need to change Word output styles.
- `.vscode/settings.json`: VS Code build recipes for LaTeX Workshop.
- `convert-docx.ps1`, `convert-docx.sh`, `scripts/`, and `filters/`: Word conversion scripts. Run them during normal writing; do not edit them unless maintaining the conversion pipeline.
- `.pandoc-cache/`, `.venv/`, and LaTeX auxiliary files: generated content. Do not maintain them manually and do not commit them.

## Compile PDF

In VS Code with LaTeX Workshop:

1. Open `temp.tex`.
2. Run `LaTeX Workshop: Build with recipe`.
3. Choose `latexmk` or `xelatex -> bibtex -> xelatex*2`.

Or run the full sequence manually from the repository root on either platform:

```console
xelatex -interaction=nonstopmode temp.tex
bibtex temp
xelatex -interaction=nonstopmode temp.tex
xelatex -interaction=nonstopmode temp.tex
```

The result is `temp.pdf`. If references or labels have not changed, one or two XeLaTeX runs are often enough.

## Convert To Word

Run the root shortcut for your platform.

On Windows:

```powershell
.\convert-docx.ps1
```

On Linux:

```bash
./convert-docx.sh
```

Both commands generate `temp.docx` and call the same Python core. The equivalent direct command is:

```console
uv run python scripts/tex-to-docx.py --input temp.tex --output temp.docx --bibliography reference.bib --csl gbt7714.csl --reference-doc reference.docx
```

The script automatically:

- Expands a small compatibility subset such as `\gls`, `\SI`, `\SIrange`, `\ang`, and `\bm`.
- Converts PDF figures referenced in LaTeX to PNG images that Pandoc can place in Word more reliably.
- Runs Pandoc and the Lua filter to generate DOCX.
- Adds three-line-table borders and table paragraph styles in Word, centers tables, and enables autofit width.
- Normalizes project style IDs in the Word document to use the `Lpt...` prefix.

For custom input, output, bibliography, style template, or image DPI, pass `--input`, `--output`, `--bibliography`, `--csl`, `--reference-doc`, or `--image-dpi` to either root shortcut or the Python command.

## Word Style Template

Project style IDs in `reference.docx` use the `Lpt...` prefix, such as `LptHeading1`, `LptBodyText`, `LptTableCaption`, and `LptReferenceItem`, to avoid conflicts with Word or Pandoc built-in style IDs.

After replacing or regenerating `reference.docx`, run:

```console
uv run python scripts/namespace-reference-docx-styles.py reference.docx
```

When adjusting heading styles, do not manually type numbers such as `1` or `1.1` in the body of `reference.docx`. Heading numbering should be bound through Word multilevel lists to `LptHeading1`, `LptHeading2`, and `LptHeading3`. The script above repairs those numbering relationships.

## Writing Tips

- Keep title, authors, abstract, and keywords at the beginning of the manuscript.
- Use `\section`, `\subsection`, and `\subsubsection` for section levels.
- Use the standard `figure` environment, with one `\caption` and one `\label`.
- Prefer `booktabs` tables with `\toprule`, `\midrule`, and `\bottomrule`.
- Use the standard `equation` environment and add `\label` for equations.
- Use ordinary `\cite{...}` commands for references.

Avoid complex journal-template commands during drafting, such as custom two-column layout, headers and footers, complex title pages, or bilingual caption counter fallbacks. These can be handled later when moving the finished manuscript to the target journal template.

## Figures

For LaTeX PDF output, PDF vector figures can be used directly. During Word conversion, `scripts/prepare-pandoc-images.py` automatically renders PDF figures referenced by `\includegraphics` to PNG and writes them to `.pandoc-cache/images/`.

Regular PNG and JPG images can be placed in `fig/` and referenced directly.

## Git Notes

Generated files are ignored by `.gitignore`, including:

- `*.pdf`
- `*.docx`
- LaTeX auxiliary files
- `.pandoc-cache/`
- `.venv/`

Usually, only source files, scripts, filters, reference files, and figure assets that should be kept in `fig/` need to be committed.

## Contributing

Contributions are welcome, especially in these areas:

- Report problems encountered during LaTeX compilation or Pandoc-to-Word conversion.
- Improve beginner-friendly usage documentation.
- Improve the Word style template, figure/table formatting, or reference formatting.
- Share compatibility issues and fixes from different manuscript writing scenarios.

Before submitting changes, make sure generated files are not included by accident. For non-trivial changes, use commit message body bullets to describe the main changes clearly.

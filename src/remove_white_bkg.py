# /// script
# dependencies = [
#   "pdfrw",
#   "rich",
# ]
# ///


import logging
from rich.logging import RichHandler
import pdfrw
from pdfrw import PdfReader, PdfWriter, PdfDict
from pathlib import Path
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%X",
    handlers=[
        RichHandler(
            markup=True,
            rich_tracebacks=True,
        ),
    ],
)
logger = logging.getLogger("remove_white_bkg")


def white_to_transparent_fill(pdf_path: Path, pdf_path_out: Path) -> None:
    doc = PdfReader(pdf_path)
    pages = doc.pages
    for page in doc.pages:
        logger.info(f"Processing page {page} in {pdf_path.name}")
        pdfrw.uncompress.uncompress([page.Contents])

        page.Contents.stream = page.Contents.stream.replace("\n1 g", "\n/JH0 gs 1 g")
        page.Contents.stream = page.Contents.stream.replace("\n/A1 gs", "\n/JH0 gs")

        # Create transparency graphics state
        transparent_gs = PdfDict()
        transparent_gs.Type = "/ExtGState"
        transparent_gs.ca = 0
        transparent_gs.CA = 0
        if not page.Resources:
            page.Resources = PdfDict()
        if not page.Resources.ExtGState:
            page.Resources.ExtGState = PdfDict()
        page.Resources.ExtGState.JH0 = transparent_gs

        pdfrw.compress.compress([page.Contents])

    pdf_out = PdfWriter()
    for page in pages:
        pdf_out.addpage(page)
    pdf_out.write(pdf_path_out)


@dataclass
class Args:
    input_paths: list[Path]
    suffix: str

    def __init__(self, argv: list[str] | None = None):
        import argparse

        parser = argparse.ArgumentParser(
            description="Remove large white rectangles from PDF files.",
        )
        parser.add_argument(
            "input_paths",
            nargs="+",
            type=Path,
            help="PDF files or folders containing PDF files to process",
        )
        parser.add_argument(
            "--suffix",
            type=str,
            default="_clean",
            help="Suffix for cleaned PDF files",
        )

        args = parser.parse_args(argv)

        self.input_paths = [Path(i) for i in args.input_paths]
        self.suffix = args.suffix


def main():
    args = Args()

    pdf_files = []
    for pdf in args.input_paths:
        if pdf.is_file():
            pdf_files.append(pdf)
        elif pdf.is_dir():
            pdf_files.extend(pdf.glob("*.pdf"))
        else:
            logger.info(f"Skipping {pdf}, not a file or directory.")
            continue

    pdf_files = [pdf for pdf in pdf_files if pdf.suffix.lower() == ".pdf"]
    pdf_files = [pdf for pdf in pdf_files if args.suffix not in pdf.stem]

    for pdf_file in pdf_files:
        logger.info(f"Processing {pdf_file}")
        pdf_out = pdf_file.with_name(f"{pdf_file.stem}{args.suffix}.pdf")
        white_to_transparent_fill(pdf_file, pdf_out)
        logger.info(f"Processed {pdf_file} -> {pdf_out}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        exit(1)
    else:
        exit(0)

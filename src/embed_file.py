# /// script
# dependencies = [
#   "pymupdf",
#   "rich",
# ]
# ///

import pymupdf
import logging
from rich.logging import RichHandler
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


@dataclass
class Args:
    pdf: Path
    embed_files: list[Path] = None
    verbose: bool = False

    def __init__(self, argv: list[str] | None = None):
        import argparse

        parser = argparse.ArgumentParser(
            description="Remove large white rectangles from PDF files.",
        )
        parser.add_argument(
            "pdf",
            metavar="PDF_FILE",
            type=Path,
            help="PDF file to embed files into.",
        )
        parser.add_argument(
            "embed_files",
            metavar="EMBED_FILE",
            nargs="+",
            type=Path,
            help="Files to embed into the PDF.",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose logging.",
        )

        args = parser.parse_args(argv)
        self.pdf = args.pdf
        self.embed_files = args.embed_files
        self.verbose = args.verbose


def embed_data(
    pdf_path: Path,
    data: bytes,
    name: str,
    pdf_out: Path | None = None,
    logger: logging.Logger = logger,
) -> None:
    """
    Embed a file into a PDF document.
    :param pdf_path: Path to the PDF file.
    :param data: Data of the file to embed.
    :param name: Name of the embedded file.
    :param pdf_out: Path to save the modified PDF. If None, it will overwrite the original PDF.
    :return: None
    """
    with pymupdf.open(pdf_path) as doc:
        logger.info(f"Processing {pdf_path}")
        logger.debug(f"Adding embedded file: {name} with size {len(data)} bytes")
        doc.embfile_add(name, data)

        kwargs = {}
        if pdf_out is None:
            if doc.can_save_incrementally():
                pdf_out = pdf_path
                kwargs["encryption"] = pymupdf.PDF_ENCRYPT_KEEP
                kwargs["incremental"] = True
            else:
                pdf_out = pdf_path.with_name(f"{pdf_path.stem}_embedded.pdf")
        doc.save(pdf_out, **kwargs)


def read_embedded_files(
    pdf_path: Path,
    logger: logging.Logger = logger,
) -> None:
    """
    Print the names and contents of embedded files in a PDF document.
    :param pdf_path: Path to the PDF file.
    :return: None
    """
    embeds = {}
    with pymupdf.open(pdf_path) as doc:
        for name in doc.embfile_names():
            content = doc.embfile_get(name)
            if content:
                logger.debug(f"Content of {name}:\n{content.decode('utf-8')}")
                embeds[name] = content
    return embeds


def print_embedded_files(
    pdf_path: Path,
    logger: logging.Logger = logger,
) -> None:
    """
    Print the names and contents of embedded files in a PDF document.
    :param pdf_path: Path to the PDF file.
    :return: None
    """
    with pymupdf.open(pdf_path) as doc:
        for name in doc.embfile_names():
            content = doc.embfile_get(name)
            if content:
                logger.debug(f"Content of {name}:\n{content.decode('utf-8')}")


def main() -> int:
    args = Args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.debug(f"Arguments: {args}")

    pdf_out = args.pdf.with_name(f"{args.pdf.stem}_with_embeds.pdf")

    for embed_file in args.embed_files:
        if not embed_file.exists():
            logger.error(f"File {embed_file} does not exist.")
            return 1
        with open(embed_file, "rb") as f:
            contents = f.read()
        try:
            embed_data(args.pdf, contents, name=embed_file.name)
        except Exception as e:
            logger.exception(f"Failed to process {embed_file}: {e}")
            return 1

    print_embedded_files(pdf_out)

    return 0


if __name__ == "__main__":
    exit(main())

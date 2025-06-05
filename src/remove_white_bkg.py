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
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Tuple


WHITE_COLOR_THRESHOLD = 0.95
DEFAULT_AREA_THRESHOLD = 0.5

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


def is_large_white_rectangle(
    rect: pymupdf.Rect,
    fill: Tuple[float, float, float, float] | None,
    page_area: float,
    threshold: float = DEFAULT_AREA_THRESHOLD,
    logger: logging.Logger = logger,
) -> bool:
    """Check if rectangle is large and white."""
    area = rect.width * rect.height
    frac = area / page_area
    logger.info(f"Found white rectangle with {frac:.0%} of page area and fill {fill}")

    if not fill:
        return False
    area = rect.width * rect.height
    frac = area / page_area
    is_white = all(c >= WHITE_COLOR_THRESHOLD for c in fill[:3])

    is_large_white_rect = frac > threshold and is_white

    if is_large_white_rect:
        logger.info(f"Found large white rectangle with {frac:.0%} of page area.")
    return is_large_white_rect


def remove_large_white_rectangles(
    doc: pymupdf.Document,
    pdf_out: Path | None,
    threshold: float = DEFAULT_AREA_THRESHOLD,
    logger: logging.Logger = logger,
) -> None:
    changes_made = False
    outpdf = pymupdf.open()
    for page in doc:
        page_area = page.rect.width * page.rect.height

        outpage = outpdf.new_page(
            width=page.rect.width,
            height=page.rect.height,
        )
        shape = outpage.new_shape()
        for path in page.get_drawings(
            extended=True,  # include extended attributes
        ):
            logger.debug(f"Processing path: {path}")
            fill = path.get("fill", None)
            items = path.get("items", [])
            for item in items:
                logger.debug(f"Processing item: {item}")
                if item[0] == "l":  # line
                    shape.draw_line(item[1], item[2])
                elif item[0] == "re":  # rectangle
                    rect = item[1]
                    if is_large_white_rectangle(
                        rect, fill, page_area, threshold, logger
                    ):
                        changes_made = True
                        continue
                    shape.draw_rect(item[1])
                elif item[0] == "qu":  # quad
                    shape.draw_quad(item[1])
                elif item[0] == "c":  # curve
                    shape.draw_bezier(item[1], item[2], item[3], item[4])
                else:
                    raise ValueError("unhandled drawing", item)

            dic = {k: v for k, v in path.items() if v and k not in ["items"]}
            logger.debug(f"Processing path with {len(dic)} attributes: {dic}")

            shape.finish(
                fill=dic.get("fill", None),  # fill color
                color=dic.get("color", None),  # line color
                dashes=dic.get("dashes", None),  # line dashing
                even_odd=dic.get("even_odd", True),  # control color of overlaps
                closePath=dic.get(
                    "closePath", False
                ),  # whether to connect last and first point
                lineJoin=dic.get("lineJoin", 0),  # how line joins should look like
                lineCap=max(dic.get("lineCap", [0])),  # how line ends should look like
                width=dic.get("width", None),  # line width
                stroke_opacity=dic.get("stroke_opacity", 1),  # same value for both
                fill_opacity=dic.get("fill_opacity", 1),  # opacity parameters
                oc=0,  # optional, for overprint control
            )
        shape.commit()

        # text_dict = page.get_text("dict")
        # for block in text_dict["blocks"]:
        #     logger.debug(f"Processing text block: {block}")
        #     if "lines" in block:
        #         for line in block["lines"]:
        #             for span in line["spans"]:
        #                 # Extract text properties
        #                 text = span["text"]
        #                 font = span["font"]
        #                 size = span["size"]
        #                 flags = span["flags"]  # bold, italic, etc.
        #                 color = span["color"]
        #                 bbox = span["bbox"]

        #                 # Calculate insertion point (bottom-left of text)
        #                 insert_point = (bbox[0], bbox[3])

        #                 # Insert text on the output page
        #                 outpage.insert_text(
        #                     insert_point,
        #                     text,
        #                     fontname=font,
        #                     fontsize=size,
        #                     color=color,
        #                     flags=flags,
        #                 )
        #                 logger.debug("Draw debug box around text: %s", bbox)
        #                 shape.draw_rect(bbox)
        #                 shape.finish(
        #                     fill=(0,),
        #                     color=(0,),
        #                     dashes=None,
        #                     even_odd="even_odd",
        #                     closePath=False,
        #                     lineJoin=0,
        #                     lineCap=[0],
        #                     width=1,
        #                     stroke_opacity=1,
        #                     fill_opacity=1,
        #                     oc=0,
        #                 )

        if not changes_made:
            return
        outpdf.save(pdf_out)  # , garbage=4, deflate=True, clean=True)


@dataclass
class Args:
    input_paths: list[Path]
    suffix: str
    threshold: float

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
        parser.add_argument(
            "--threshold",
            type=float,
            default=DEFAULT_AREA_THRESHOLD,
            help="Fraction of page area that a rectangle must exceed to be removed",
        )
        args = parser.parse_args(argv)

        self.input_paths = [Path(i) for i in args.input_paths]
        self.suffix = args.suffix
        self.threshold = args.threshold


def process_file(
    pdf_file: Path,
    suffix: str | None = None,
    threshold: float = DEFAULT_AREA_THRESHOLD,
    logger: logging.Logger = logger,
) -> None:
    logger.info(f"Processing {pdf_file}")

    pdf_out = pdf_file
    if suffix:
        pdf_out = pdf_file.with_name(f"{pdf_file.stem}{suffix}.pdf")

    with pymupdf.open(pdf_file) as doc:
        remove_large_white_rectangles(doc, pdf_out, threshold)


def main() -> int:
    args = Args()

    pdf_files = []
    for path in args.input_paths:
        if path.is_file():
            pdf_files.append(path)
        elif path.is_dir():
            pdf_files.extend(path.glob("**/*.pdf"))
    pdf_files = [p for p in pdf_files if p.is_file() and p.suffix.lower() == ".pdf"]

    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(process_file, pdf, args.suffix, args.threshold)
            for pdf in pdf_files
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.exception(f"Error processing file: {e}")
    return 0


if __name__ == "__main__":
    exit(main())

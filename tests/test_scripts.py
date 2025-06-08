def test_embed(plot_01_pdf):
    assert plot_01_pdf.exists(), "The plot_01.pdf file should exist after plotting."

    from src.embed_file import embed_data, read_embedded_files

    data = b"Sample embedded data"
    name = "sample_data.txt"
    embed_data(plot_01_pdf, data, name)
    embedded_files = read_embedded_files(plot_01_pdf)
    assert name in embedded_files, f"{name} should be in the embedded files."
    assert embedded_files[name] == data, (
        f"The content of {name} should match the embedded data."
    )


def test_remove_white_bkg(plot_02_pdf):
    """
    Test the remove_white_bkg function.
    This function should be defined in the embed_file module.
    """

    from src.remove_white_bkg import white_to_transparent_fill

    pdf = plot_02_pdf

    pdf_out = pdf.with_name(f"{pdf.stem}_clean.pdf")

    white_to_transparent_fill(pdf, pdf_out)

    # Check if the output file exists
    assert pdf_out.exists(), f"{pdf_out} should exist after processing."
    print(pdf)

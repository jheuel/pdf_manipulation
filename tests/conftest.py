import pytest


@pytest.fixture
def plot_01_pdf(tmp_path):
    """
    Fixture to generate the PDF from plot_01, replacing test_01.
    Yields the path to the generated PDF for postprocessing.
    """
    from tests.samples import plot_01

    plot_path = tmp_path / "plot_01.pdf"
    plot_01.plot(plot_path)

    assert plot_path.exists(), f"{plot_path} was not created."
    yield plot_path


@pytest.fixture
def plot_02_pdf(tmp_path):
    """
    Fixture to generate the PDF from plot_02, replacing test_01.
    Yields the path to the generated PDF for postprocessing.
    """
    from tests.samples import plot_02

    plot_path = tmp_path / "plot_02.pdf"
    plot_02.plot(plot_path)

    assert plot_path.exists(), f"{plot_path} was not created."
    yield plot_path

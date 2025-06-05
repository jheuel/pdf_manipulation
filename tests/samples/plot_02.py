# /// script
# dependencies = [
#   "matplotlib",
# ]
# ///

import matplotlib.pyplot as plt


def plot(path: str | None = None):
    fig = plt.figure()
    ax = fig.add_axes((0.1, 0.2, 0.8, 0.7))
    ax.bar([0, 1], [0, 100], 0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.xaxis.set_ticks_position("bottom")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["CONFIRMED BY\nEXPERIMENT", "REFUTED BY\nEXPERIMENT"])
    ax.set_xlim([-0.5, 1.5])
    ax.set_yticks([])
    ax.set_ylim([0, 110])

    ax.set_title("CLAIMS OF SUPERNATURAL POWERS")

    fig.text(0.5, 0.035, '"The Data So Far" from xkcd by Randall Munroe', ha="center")

    fig.savefig(path)


if __name__ == "__main__":
    plot("plot_01.pdf")

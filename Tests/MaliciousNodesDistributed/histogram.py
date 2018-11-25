from collections import Counter
import numpy as np
import matplotlib.pyplot as plt

a = ['a', 'a', 'a', 'a', 'b', 'b', 'c', 'c', 'c', 'd', 'e', 'e', 'e', 'e', 'e']
letter_counts = Counter(a)

def plot_bar_from_counter(counter, ax=None):
    """"
    This function creates a bar plot from a counter.

    :param counter: This is a counter object, a dictionary with the item as the key
     and the frequency as the value
    :param ax: an axis of matplotlib
    :return: the axis wit the object in it
    """

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)

    frequencies = counter.values()
    names = counter.keys()

    x_coordinates = np.arange(len(counter))
    ax.bar(x_coordinates, frequencies, align='center')

    ax.xaxis.set_major_locator(plt.FixedLocator(x_coordinates))
    ax.xaxis.set_major_formatter(plt.FixedFormatter(names))

    return ax




def plot_histogram(times, filename):
    '''
    Plots the histogram of the completion times of the various phases
    :param times: list of times. The times must be sorted: [open, establish, accept, total]
    :param name: The filename of the plot on disk
    '''
    xvals = range(4)
    xnames=["Open","Establish","Accept","Total"]
    yvals = times
    width = 0.25
    yinterval = 10

    figure = plt.figure()
    plt.grid(True)
    plt.xlabel('Phases')
    plt.ylabel('Average Completion Times')

    plt.bar(xvals, yvals, width=width, align='center')
    plt.xticks(xvals, xnames)
    plt.yticks(range(0,max(yvals),yinterval))
    plt.xlim([min(xvals) - 0.5, max(xvals) + 0.5])

    figure.savefig(filename,format="png")
    plt.show()




plot_bar_from_counter(letter_counts)
plt.show()
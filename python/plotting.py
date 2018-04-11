#!/usr/bin/env python

__author__ = "Sam Way"
__copyright__ = "Copyright 2018, The Clauset Lab"
__license__ = "BSD"
__maintainer__ = "Sam Way"
__email__ = "samfway@gmail.com"
__status__ = "Development"


import numpy as np
from matplotlib import rcParams


# Constants
SINGLE_FIG_SIZE = (6,4)
BAR_WIDTH = 0.6
TICK_SIZE = 15
XLABEL_PAD = 10
LABEL_SIZE = 14
TITLE_SIZE = 16
LEGEND_SIZE = 12
LINE_WIDTH = 2
LIGHT_COLOR = '0.8'
LIGHT_COLOR_V = np.array([float(LIGHT_COLOR) for i in range(3)])
DARK_COLOR = '0.4'
DARK_COLOR_V = np.array([float(DARK_COLOR) for i in range(3)])
ALMOST_BLACK = '0.125'
ALMOST_BLACK_V = np.array([float(ALMOST_BLACK) for i in range(3)])
ACCENT_COLOR_1 = np.array([0.40254901960784313, 0.75274509803921569, 0.50254901960784313])  # Green from the WWW paper


# Color declarations
COLOR_M = ALMOST_BLACK
COLOR_F = ACCENT_COLOR_1
COLOR_PRIVATE = np.array([176, 116, 232])/255.
COLOR_PUBLIC = np.array([32, 32, 32])/255.


# Configuration
#rcParams['text.usetex'] = True #Let TeX do the typsetting
rcParams['pdf.use14corefonts'] = True
rcParams['ps.useafm'] = True
rcParams['font.family'] = 'sans-serif' # ... for regular text
rcParams['font.sans-serif'] = ['Helvetica Neue', 'HelveticaNeue', 'Helvetica'] #, Avant Garde, Computer Modern Sans serif' # Choose a nice font here
rcParams['pdf.fonttype'] = 42
rcParams['ps.fonttype'] = 42
rcParams['text.color'] = ALMOST_BLACK
rcParams['axes.unicode_minus'] = False


rcParams['xtick.major.pad'] = '8'
rcParams['axes.edgecolor']  = ALMOST_BLACK
rcParams['axes.labelcolor'] = ALMOST_BLACK
rcParams['lines.color']     = ALMOST_BLACK
rcParams['xtick.color']     = ALMOST_BLACK
rcParams['ytick.color']     = ALMOST_BLACK
rcParams['text.color']      = ALMOST_BLACK
rcParams['lines.solid_capstyle'] = 'butt'


# Imports
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D


def finalize(ax, fontsize=LABEL_SIZE, labelpad=7):
    """ Apply final adjustments """ 
    ax.tick_params(direction='out')
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.yaxis.label.set_size(fontsize)
    ax.xaxis.label.set_size(fontsize)
    ax.tick_params(axis='both', which='major', labelsize=fontsize, pad=labelpad)


def custom_legend_handles(markers, colors, markersizes, **kwargs):
    
    # For now, assume everything has the same length
    assert(len(markers) == len(colors))
    assert(len(colors) == len(markersizes))
    
    handles = []
    for i in range(len(markers)):
        handles.append(Line2D(range(1), range(1), color=colors[i], marker=markers[i], markersize=markersizes[i], 
                             linestyle='None', markeredgecolor='w', **kwargs))
        
    return handles

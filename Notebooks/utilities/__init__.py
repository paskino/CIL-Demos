# imports for plotting
from __future__ import print_function
from __future__ import division
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy
import numpy as np

def display_slice(datacontainer, direction, title='Title '):
    container = datacontainer.as_array()
    
    def get_slice_3D(x):
        
        if direction == 0:
            img = container[x]
        elif direction == 1:
            img = container[:,x,:]
        elif direction == 2:
            img = container[:,:,x]
        fig = plt.figure()
        gs = gridspec.GridSpec(1, 2, figure=fig, width_ratios=(1,.05))
        # image
        ax = fig.add_subplot(gs[0, 0])
        aximg = ax.imshow(img)
        ax.set_title(title + "slice {}".format(x))
        # colorbar
        ax = fig.add_subplot(gs[0, 1])
        plt.colorbar(aximg, cax=ax)
        plt.tight_layout()          
        plt.show()
        
    return get_slice_3D
    
def islicer(data, direction):
    '''Creates an interactive integer slider that slices a 3D volume along direction
    
    :param data: DataContainer
    :param direction: slice direction, int, should be 0,1,2 or the axis label
    '''
    if direction in data.dimension_labels.values():
        direction = data.get_dimension_axis(direction)
    interact(display_slice(data,direction), 
         x=widgets.IntSlider(min=0, max=data.shape[direction]-1, step=1, 
                             value=0, continuous_update=False));
    
    

def setup_iplot2D(x_init):
    '''creates a matplotlib figure'''
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.ion()
    im = fig.add_subplot(122)
    im.imshow(x_init.as_array())
    fig.show()
    fig.canvas.draw()

    residuals = []
    iterations = []
    return fig, ax, im, iterations, residuals
    


def iplot2D(fig, ax, im, iterations, residuals):
    '''callback to change the matplotlib figure created with setup_iplot2D'''
    def update(iteration, last_objective, x):
        residuals.append(last_objective)
        iterations.append(iteration)
        ax.clear()
        ax.plot(iterations, residuals)
        im.imshow(x.as_array())
        fig.canvas.draw()
    return update

def plotter2D(datacontainers, titles, fix_range=False, stretch_y=False):
    '''plotter2D(datacontainers, titles, fix_range=False, stretch_y=False)
    
    plots 1 or more 2D plots in an (n x 2) matix
    multiple datasets can be passed as a list
    
    Can take ImageData, AquistionData or numpy.ndarray as input
    '''
    if(isinstance(datacontainers, list)) is False:
        datacontainers = [datacontainers]

    if(isinstance(titles, list)) is False:
        titles = [titles]
    
    nplots = len(datacontainers)
    rows = int(round((nplots+0.5)/2.0))

    fig, (ax) = plt.subplots(rows, 2,figsize=(15,15))

    axes = ax.flatten() 

    range_min = float("inf")
    range_max = 0
    
    if fix_range == True:
        for i in range(nplots):
            if type(datacontainers[i]) is np.ndarray:
                dc = datacontainers[i]
            else:
                dc = datacontainers[i].as_array()
                
            range_min = min(range_min, np.amin(dc))
            range_max = max(range_max, np.amax(dc))
        
    for i in range(rows*2):
        axes[i].set_visible(False)

    for i in range(nplots):
        axes[i].set_visible(True)
        axes[i].set_title(titles[i])
       
        if type(datacontainers[i]) is np.ndarray:
            dc = datacontainers[i]
        else:
            dc = datacontainers[i].as_array()    
        
        sp = axes[i].imshow(dc)
        
        im_ratio = dc.shape[0]/dc.shape[1]
        
        if stretch_y ==True:   
            axes[i].set_aspect(1/im_ratio)
            im_ratio = 1
            
        plt.colorbar(sp, ax=axes[i],fraction=0.0467*im_ratio, pad=0.02)
        
        if fix_range == True:
            sp.set_clim(range_min,range_max)
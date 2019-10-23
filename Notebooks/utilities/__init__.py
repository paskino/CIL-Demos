# imports for plotting
from __future__ import print_function
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy

def display_slice(container, direction, title, cmap, minmax, size):
    
        
    def get_slice_3D(x):
        
        if direction == 0:
            img = container[x]
        elif direction == 1:
            img = container[:,x,:]
        elif direction == 2:
            img = container[:,:,x]
        if size is None:
            fig = plt.figure()
        else:
            fig = plt.figure(figsize=size)
                  
        gs = gridspec.GridSpec(1, 2, figure=fig, width_ratios=(1,.05), height_ratios=(1,))
        # image
        ax = fig.add_subplot(gs[0, 0])
        aximg = ax.imshow(img, cmap=cmap)
        aximg.set_clim(minmax)
        ax.set_title(title + " {}".format(x))
        # colorbar
        ax = fig.add_subplot(gs[0, 1])
        plt.colorbar(aximg, cax=ax)
        plt.tight_layout()
        plt.show(fig)
        
    return get_slice_3D

    
def islicer(data, direction, title="", slice_number=None, cmap='gnuplot', minmax=None, size=None):

    '''Creates an interactive integer slider that slices a 3D volume along direction
    
    :param data: DataContainer or numpy array
    :param direction: slice direction, int, should be 0,1,2 or the axis label
    :param title: optional title for the display
    :param cmap: matplotlib color map
    :param minmax: colorbar min and max values, defaults to min max of container
    '''
    
    if hasattr(data, "as_array"):
        container = data.as_array()
        if not isinstance (direction, int):
            if direction in data.dimension_labels.values():
                direction = data.get_dimension_axis(direction)
    elif isinstance (data, numpy.ndarray):
        container = data
        
    if slice_number is None:
        slice_number = int(data.shape[direction]/2)
    slider = widgets.IntSlider(min=0, max=data.shape[direction]-1, step=1, 
                             value=slice_number, continuous_update=False)

    #figure_size = kwargs.get('figure_size', (10,10))
    figure_size= (10,10)
    
    if minmax is None:
        amax = container.max()
        amin = container.min()
    else:
        amin = min(minmax)
        amax = max(minmax)
    
    if isinstance (size, (int, float)):
        default_ratio = 6./8.
        size = ( size , size * default_ratio )
    
    interact(display_slice(container, 
                           direction, 
                           title=title, 
                           cmap=cmap, 
                           minmax=(amin, amax),
                           size=size),
             x=slider);
    return slider
    

def link_islicer(*args):
    '''links islicers IntSlider widgets'''
    linked = [(widg, 'value') for widg in args]
    # link pair-wise
    pairs = [(linked[i+1],linked[i]) for i in range(len(linked)-1)]
    for pair in pairs:
        widgets.link(*pair)




def psnr(img1, img2, data_range=1):
    mse = numpy.mean( (img1 - img2) ** 2 )
    if mse == 0:
        return 1000
    return 20 * numpy.log10(data_range / numpy.sqrt(mse))


def plotter2D(datacontainers, titles, fix_range=False, stretch_y=False, cmap='gnuplot'):
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
            if type(datacontainers[i]) is numpy.ndarray:
                dc = datacontainers[i]
            else:
                dc = datacontainers[i].as_array()
                
            range_min = min(range_min, numpy.amin(dc))
            range_max = max(range_max, numpy.amax(dc))
        
    for i in range(rows*2):
        axes[i].set_visible(False)

    for i in range(nplots):
        axes[i].set_visible(True)
        axes[i].set_title(titles[i])
       
        if type(datacontainers[i]) is numpy.ndarray:
            dc = datacontainers[i]
        else:
            dc = datacontainers[i].as_array()    
        
        sp = axes[i].imshow(dc, cmap=cmap)
        
        im_ratio = dc.shape[0]/dc.shape[1]
        
        if stretch_y ==True:   
            axes[i].set_aspect(1/im_ratio)
            im_ratio = 1
            
        plt.colorbar(sp, ax=axes[i],fraction=0.0467*im_ratio, pad=0.02)
        
        if fix_range == True:
            sp.set_clim(range_min,range_max)


# imports for plotting
from __future__ import print_function
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy

def display_slice(container, direction, title, cmap, minmax):
    
        
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
        aximg = ax.imshow(img, cmap=cmap)
        aximg.set_clim(minmax)
        ax.set_title(title + " {}".format(x))
        # colorbar
        ax = fig.add_subplot(gs[0, 1])
        plt.colorbar(aximg, cax=ax)
        plt.tight_layout()
        plt.show(fig)
        
    return get_slice_3D

    
def islicer(data, direction, title="", cmap='viridis', minmax=None, **kwargs):
    '''Creates an interactive integer slider that slices a 3D volume along direction
    
    :param data: DataContainer or numpy array
    :param direction: slice direction, int, should be 0,1,2 or the axis label
    :param title: optional title for the display
    '''
    
    if hasattr(data, "as_array"):
        container = data.as_array()
        if not isinstance (direction, int):
            if direction in data.dimension_labels.values():
                direction = data.get_dimension_axis(direction)
    elif isinstance (data, numpy.ndarray):
        container = data
      
    slice_number = kwargs.get( 'slice_number', 0)    
    
    slider = widgets.IntSlider(min=0, max=data.shape[direction]-1, step=1, 
                             value=slice_number, continuous_update=False)

    figure_size = kwargs.get('figure_size', (10,10))
    
    if minmax is None:
        amax = container.max()
        amin = container.min()
    else:
        amin = min(minmax)
        amax = max(minmax)
    
    interact(display_slice(container, 
                           direction, 
                           title=title, 
                           cmap=cmap,
                           minmax=(amin, amax)),
             x=slider);
    return slider
    

def link_islicer(*args):
    '''links islicers IntSlider widgets'''
    linked = [(widg, 'value') for widg in args]
    # link pair-wise
    pairs = [(linked[i+1],linked[i]) for i in range(len(linked)-1)]
    for pair in pairs:
        widgets.link(*pair)

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
    


def psnr(img1, img2, data_range=1):
    mse = numpy.mean( (img1 - img2) ** 2 )
    if mse == 0:
        return 1000
    return 20 * numpy.log10(data_range / numpy.sqrt(mse))

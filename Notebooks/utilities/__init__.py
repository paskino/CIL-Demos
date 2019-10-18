# imports for plotting
from __future__ import print_function
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy

def display_slice(container, direction, title='Title '):
    
        
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
        plt.show(fig)
        
    return get_slice_3D
    
def islicer(data, direction, title=""):
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
        
    
    slider = widgets.IntSlider(min=0, max=data.shape[direction]-1, step=1, 
                             value=0, continuous_update=False)


    interact(display_slice(container, direction, title=title), x=slider);
    return slider
    

def link_islicer(*args):
    '''links islicers IntSlider widgets'''
    linked = [(widg, 'value') for widg in args]
    widgets.link(*linked)
    

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


def dothis(x, **kwargs):
    sliceno = kwargs.get('sliceno', 0)
    cmd = "x.subset("
    for k,v in kwargs.items():
        # print (k,v)
        if k in x.dimension_labels.values():
            cmd += "{}={}".format(k,sliceno)
            break
    cmd += ")"
    # print (cmd)
    return eval(cmd)

def setup_iplot3D(x_init, **kwargs):
    '''creates a matplotlib figure'''
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.ion()
    im = fig.add_subplot(122)
    im.imshow(dothis(x_init, **kwargs).as_array())
    fig.show()
    fig.canvas.draw()

    residuals = []
    iterations = []
    return fig, ax, im, iterations, residuals
    
def iplot3D(fig, ax, im, iterations, residuals, **kwargs):
    '''callback to change the matplotlib figure created with setup_iplot2D'''
    
    
    def update(iteration, last_objective, x):
        residuals.append(last_objective)
        iterations.append(iteration)
        ax.clear()
        ax.plot(iterations, residuals)
        im.imshow(dothis(x, **kwargs).as_array())
        fig.canvas.draw()
    return update
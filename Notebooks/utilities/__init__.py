# imports for plotting
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import matplotlib.pyplot as plt
from matplotlib import gridspec


def display_slice(datacontainer, direction, title='Title'):
    
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
        ax.set_title("{} {}".format(title, x))
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

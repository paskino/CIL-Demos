# imports for plotting
from __future__ import print_function
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import matplotlib.pyplot as plt
from matplotlib import gridspec


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
    
def interactive_slice_display(data, direction):
    '''Creates an interactive integer slider that slices a 3D volume along direction
    
    :param data: DataContainer
    :param direction: slice direction, int, should be 0,1,2 or the axis label
    '''
    if direction in data.dimension_labels.values():
        direction = data.get_dimension_axis(direction)
    interact(display_slice(data,direction), 
         x=widgets.IntSlider(min=0, max=data.shape[direction]-1, step=1, 
                             value=0, continuous_update=False));
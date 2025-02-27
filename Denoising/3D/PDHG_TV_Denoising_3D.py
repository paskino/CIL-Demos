#========================================================================
# Copyright 2019 Science Technology Facilities Council
# Copyright 2019 University of Manchester
#
# This work is part of the Core Imaging Library developed by Science Technology
# Facilities Council and University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#=========================================================================
""" 

Total Variation (3D) Denoising using PDHG algorithm and Tomophantom:


Problem:     min_{x} \alpha * ||\nabla x||_{2,1} + \frac{1}{2} * || x - g ||_{2}^{2}

             \alpha: Regularization parameter
             
             \nabla: Gradient operator 
             
             g: 3D Noisy Data with Gaussian Noise
                          
             Method = 0 ( PDHG - split ) :  K = [ \nabla,
                                                 Identity]
                          
                                                                    
             Method = 1 (PDHG - explicit ):  K = \nabla  
                                                                
"""

from ccpi.framework import ImageData, ImageGeometry, TestData                       
import matplotlib.pyplot as plt
from ccpi.optimisation.algorithms import PDHG
from ccpi.optimisation.operators import Gradient
from ccpi.optimisation.functions import L2NormSquared, MixedL21Norm

import timeit
import os
import sys
from tomophantom import TomoP3D
import tomophantom
import numpy

# Create a phantom from Tomophantom
print ("Building 3D phantom using TomoPhantom software")
tic=timeit.default_timer()
model = 13 # select a model number from the library
N = 64 # Define phantom dimensions using a scalar value (cubic phantom)
path = os.path.dirname(tomophantom.__file__)
path_library3D = os.path.join(path, "Phantom3DLibrary.dat")

#This will generate a N x N x N phantom (3D)
phantom_tm = TomoP3D.Model(model, N, path_library3D)

# Create noisy data. Apply Gaussian noise
ig = ImageGeometry(voxel_num_x=N, voxel_num_y=N, voxel_num_z=N)
ag = ig
n1 = TestData.random_noise(phantom_tm, mode = 'gaussian', mean=0, var = 0.001, seed=10)
noisy_data = ImageData(n1)

# Show results
sliceSel = int(0.5*N)
plt.figure(figsize=(15,15))
plt.subplot(3,1,1)
plt.imshow(noisy_data.as_array()[sliceSel,:,:],vmin=0, vmax=1)
plt.title('Axial View')
plt.colorbar()
plt.subplot(3,1,2)
plt.imshow(noisy_data.as_array()[:,sliceSel,:],vmin=0, vmax=1)
plt.title('Coronal View')
plt.colorbar()
plt.subplot(3,1,3)
plt.imshow(noisy_data.as_array()[:,:,sliceSel],vmin=0, vmax=1)
plt.title('Sagittal View')
plt.colorbar()
plt.show()   

# Regularisation Parameter
alpha = 0.05
    
# Setup and run the PDHG algorithm
operator = Gradient(ig)
f =  alpha * MixedL21Norm()
g =  0.5 * L2NormSquared(b = noisy_data)
            
normK = operator.norm()

sigma = 1
tau = 1/(sigma*normK**2)

pdhg = PDHG(f=f,g=g,operator=operator, tau=tau, sigma=sigma, memopt=True)
pdhg.max_iteration = 1000
pdhg.update_objective_interval = 200
pdhg.run(1000, verbose = True)

# Show results
fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(10, 8))
fig.suptitle('TV Reconstruction',fontsize=20)

plt.subplot(2,3,1)
plt.imshow(noisy_data.as_array()[sliceSel,:,:],vmin=0, vmax=1)
plt.axis('off')
plt.title('Axial View')

plt.subplot(2,3,2)
plt.imshow(noisy_data.as_array()[:,sliceSel,:],vmin=0, vmax=1)
plt.axis('off')
plt.title('Coronal View')

plt.subplot(2,3,3)
plt.imshow(noisy_data.as_array()[:,:,sliceSel],vmin=0, vmax=1)
plt.axis('off')
plt.title('Sagittal View')

plt.subplot(2,3,4)
plt.imshow(pdhg.get_output().as_array()[sliceSel,:,:],vmin=0, vmax=1)
plt.axis('off')
plt.subplot(2,3,5)
plt.imshow(pdhg.get_output().as_array()[:,sliceSel,:],vmin=0, vmax=1)
plt.axis('off')
plt.subplot(2,3,6)
plt.imshow(pdhg.get_output().as_array()[:,:,sliceSel],vmin=0, vmax=1)
plt.axis('off')
im = plt.imshow(pdhg.get_output().as_array()[:,:,sliceSel],vmin=0, vmax=1)


fig.subplots_adjust(bottom=0.1, top=0.9, left=0.1, right=0.8,
                    wspace=0.02, hspace=0.02)

cb_ax = fig.add_axes([0.83, 0.1, 0.02, 0.8])
cbar = fig.colorbar(im, cax=cb_ax)


plt.show()


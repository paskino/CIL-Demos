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

import timeit
import os
import matplotlib.pyplot as plt
import numpy as np
import tomophantom
from tomophantom import TomoP3D


from ccpi.framework import ImageData, ImageGeometry, AcquisitionGeometry, AcquisitionData


from ccpi.optimisation.algorithms import PDHG, FISTA, CGLS

from ccpi.optimisation.operators import BlockOperator, Gradient
from ccpi.optimisation.functions import ZeroFunction, L2NormSquared, \
                      MixedL21Norm, BlockFunction, FunctionOperatorComposition

from ccpi.astra.operators import AstraProjector3DSimple
from ccpi.plugins.regularisers import FGP_TV, SB_TV
from timeit import default_timer as timer
import astra


# Load Shepp-Logan Tomophantom 3D
print ("Building 3D phantom using TomoPhantom software")
tic=timeit.default_timer()
model = 13 # select a model number from the library
N_size = 128 # Define phantom dimensions using a scalar value (cubic phantom)
path = os.path.dirname(tomophantom.__file__)
path_library3D = os.path.join(path, "Phantom3DLibrary.dat")
#This will generate a N_size x N_size x N_size phantom (3D)
phantom_tm = TomoP3D.Model(model, N_size, path_library3D)
toc=timeit.default_timer()
Run_time = toc - tic
print("Phantom has been built in {} seconds".format(Run_time))

# Show Phantom in axial - coronal - sagittal view
slice_ind = int(N_size/2)
plt.figure(figsize = (10,30)) 
plt.subplot(131)
plt.imshow(phantom_tm[slice_ind,:,:],vmin=0, vmax=1)
plt.title('3D Phantom, axial view')

plt.subplot(132)
plt.imshow(phantom_tm[:,slice_ind,:],vmin=0, vmax=1)
plt.title('3D Phantom, coronal view')

plt.subplot(133)
plt.imshow(phantom_tm[:,:,slice_ind],vmin=0, vmax=1)
plt.title('3D Phantom, sagittal view')
plt.show()

# Parameters for Acquisition Geometry
Horiz_det = int(np.sqrt(2)*N_size) # detector column count 
Vert_det = N_size # detector row count (vertical) 
angles_num = 100 # angles number
#angles = np.linspace(0.0,179.9,angles_num,dtype='float32') # in degrees
angles_rad = np.linspace(-np.pi, np.pi, angles_num) #angles*(np.pi/180.0)

# Setup ImageGeometry and AcquisitionGeometry
ig = ImageGeometry(voxel_num_x=N_size, voxel_num_y=N_size, voxel_num_z=N_size)
ag = AcquisitionGeometry(geom_type = 'parallel', dimension = '3D', angles = angles_rad, pixel_num_h=Horiz_det, pixel_num_v=Vert_det)
Aop = AstraProjector3DSimple(ig, ag)

# Add noise to the sinogram data
X = ImageData(phantom_tm, geometry = ig)
sin = Aop.direct(X)
noisy_data = AcquisitionData(sin.as_array() + np.random.normal(0,1,ag.shape))

# Compare sinogram with the " astra - sinogram "
vol_geom = astra.create_vol_geom(N_size, N_size, N_size)
proj_geom = astra.create_proj_geom('parallel3d', 1.0, 1.0, Vert_det, Horiz_det, angles_rad)

proj_id, proj_data = astra.create_sino3d_gpu(phantom_tm, proj_geom, vol_geom)


plt.figure(figsize = (20,50)) 

plt.subplot(331)
plt.imshow(proj_data[:,slice_ind,:])
plt.colorbar()
plt.title('2D Projection (analytical)')

plt.subplot(332)
plt.imshow(proj_data[slice_ind,:,:])
plt.colorbar()
plt.title('Sinogram view')

plt.subplot(333)
plt.imshow(proj_data[:,:,slice_ind])
plt.colorbar()
plt.title('Tangentogram view')

plt.subplot(334)
plt.imshow(sin.as_array()[:,slice_ind,:])
plt.colorbar()

plt.subplot(335)
plt.imshow(sin.as_array()[slice_ind,:,:])
plt.colorbar()

plt.subplot(336)
plt.imshow(sin.as_array()[:,:,slice_ind])
plt.colorbar()

plt.subplot(337)
plt.imshow(np.abs(sin.as_array()[:,slice_ind,:] - proj_data[:,slice_ind,:]))
plt.colorbar()

plt.subplot(338)
plt.imshow(np.abs(sin.as_array()[slice_ind,:,:] - proj_data[slice_ind,:,:]))
plt.colorbar()

plt.subplot(339)
plt.imshow(np.abs(sin.as_array()[:,:,slice_ind] - proj_data[:,:,slice_ind]))
plt.colorbar()

plt.show()


#%% Run CGLS reconstruction 

# Allocate solution
x_init = ig.allocate()

cgls = CGLS(x_init=x_init, operator = Aop, data = noisy_data)
cgls.max_iteration = 100
cgls.update_objective_interval = 25
cgls.run(200, verbose = True)

# Get numpy array from  ImageData
sol_CGLS = cgls.get_output().as_array()

# Show reconstruction
plt.figure(figsize = (10,30)) 

plt.subplot(131)
plt.imshow(sol_CGLS[slice_ind,:,:],vmin=0, vmax=1)
plt.title('3D Phantom, axial view')

plt.subplot(132)
plt.imshow(sol_CGLS[:,slice_ind,:],vmin=0, vmax=1)
plt.title('3D Phantom, coronal view')

plt.subplot(133)
plt.imshow(sol_CGLS[:,:,slice_ind],vmin=0, vmax=1)
plt.title('3D Phantom, sagittal view')
plt.show()

#%% Run FISTA: Total Variation (regulariser) with L2NormSquarred ( Figelity)
# For the proximal of the Total Variation we use the ccpi-regulariser package,
# where we can choose a cpu/gpu implementation

# Cases: (a) FGP_TV: FISTA for Total Variation Denoising
#        (b) SB_TV: Split Bregman for Total Variation Denoising
#        (c) ROF_TV: Explicit PDE minimisation from the Rudin - Osher - Fatemi paper
#             Rudin, L.I., Osher, S. and Fatemi, E., 1992. Nonlinear total variation based noise removal algorithms
    
# Regulariser parameter
alpha = 10

# Select from the cases above to solve proximal-TV
g = FGP_TV(alpha, 50, 1e-6, 0,0,0, 'gpu')
#g = ROF_TV(10, 50, 1e-6, 0.025,'gpu')
#g = SB_TV(10, 50, 1e-6, 0, 0,'gpu')

# Setup fidelity term
f = FunctionOperatorComposition(L2NormSquared(b = noisy_data), Aop)

x_init = ig.allocate()

# Run FISTA for least squares
fista = FISTA(x_init = x_init, f = f, g = g)
fista.max_iteration = 1000
fista.update_objective_interval = 100
fista.run(500, verbose = True)

# Get numpy array from ImageData
sol_fista = fista.get_output().as_array()

# Show reconstruction
plt.figure(figsize = (10,30)) 

plt.subplot(131)
plt.imshow(sol_fista[slice_ind,:,:],vmin=0, vmax=1)
plt.title('3D Phantom, axial view')

plt.subplot(132)
plt.imshow(sol_fista[:,slice_ind,:],vmin=0, vmax=1)
plt.title('3D Phantom, coronal view')

plt.subplot(133)
plt.imshow(sol_fista[:,:,slice_ind],vmin=0, vmax=1)
plt.title('3D Phantom, sagittal view')
plt.show()

#%%  PDHG : Total Variation (regulariser) with L2NormSquarred ( Figelity)
# Using this algorithm, we can have explicit and implicit approaches on how we solve
# the subproblems.

# Explicit: Each subploblem is solved exactly, e.g 
#           (i) The subploblem for the Total Variation term
#           (ii) The subploblem for the Fidelity term
# For this case there is no gpu implementation for the computation of the Gradient, at the moment.

# Implicit: The subploblem for the Total Variation term is solved approximatelly
# using the ccpi-regulariser package

print(" ################################################## ")
print(" #################  PDHG Explicit ################# ")
print(" ################################################## ")      
      
op1 = Gradient(ig)
op2 = Aop

# Create BlockOperator
operator = BlockOperator(op1, op2, shape=(2,1) )
normK = operator.norm()

f2 = 0.5 * L2NormSquared(b=noisy_data)                                         
g = ZeroFunction()
sigma = 1
tau = 1/(sigma*normK**2) 

f1 = alpha * MixedL21Norm() 
f = BlockFunction(f1, f2)   

# Setup and run the PDHG algorithm
pdhg1 = PDHG(f=f,g=g,operator=operator, tau=tau, sigma=sigma)
pdhg1.max_iteration = 500
pdhg1.update_objective_interval = 50
pdhg1.run(500, verbose = True)

# Get numpy array
sol_pdhg1 = pdhg1.get_output().as_array()

print(" ################################################## ")
print(" #################  PDHG Implicit ################# ")
print(" ################################################## ")

# Here, the operator is the Astra operator
operator = op2
g2 = FGP_TV(alpha, 50, 1e-6, 0,0,0,'gpu')
sigma = 1
tau = 1/(sigma*normK**2) 

# Setup and run the PDHG algorithm
pdhg2 = PDHG(f=f2,g=g2,operator=operator, tau=tau, sigma=sigma)
pdhg2.max_iteration = 500
pdhg2.update_objective_interval = 50
pdhg2.run(500)

# Get numpy array
sol_pdhg2 = pdhg2.get_output().as_array()

#%%

plt.figure(figsize = (10,10)) 
plt.subplot(231)
plt.imshow(sol_pdhg1[slice_ind,:,:],vmin=0, vmax=1)
plt.title('PDHG Explicit, axial view')

plt.subplot(232)
plt.imshow(sol_pdhg1[:,slice_ind,:],vmin=0, vmax=1)
plt.title('PDHG Explicit, coronal view')

plt.subplot(233)
plt.imshow(sol_pdhg1[:,:,slice_ind],vmin=0, vmax=1)
plt.title('PDHG Explicit, sagittal view')

plt.subplot(234)
plt.imshow(sol_pdhg2[slice_ind,:,:],vmin=0, vmax=1)
plt.title('PDHG Implicit, axial view')

plt.subplot(235)
plt.imshow(sol_pdhg2[:,slice_ind,:],vmin=0, vmax=1)
plt.title('PDHG Implicit, coronal view')

plt.subplot(236)
plt.imshow(sol_pdhg2[:,:,slice_ind],vmin=0, vmax=1)
plt.title('PDHG Implicit, sagittal view')
plt.show()

print()
print( " PDHG Explicit: Primal/Dual/Cap {} \n".format(pdhg1.get_last_objective()))
print( " PDHG Implicit: Primal/Dual/Cap {}".format(pdhg2.get_last_objective()))
print()
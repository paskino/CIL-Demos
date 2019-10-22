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
Total Variation Color Denoising using PDHG algorithm:
    
Problem:     min_u  \alpha * ||\nabla u||_{2,1} + ||x-g||_{1}
             \alpha: Regularization parameter
             
             \nabla: Gradient operator 
             
             g: Noisy Data with Salt & Pepper Noise
             
             K = \nabla    
                          
"""

import numpy as np                        
import matplotlib.pyplot as plt

from ccpi.optimisation.algorithms import PDHG

from ccpi.optimisation.operators import Gradient, BlockOperator, Identity, SymmetrizedGradient, ZeroOperator
from ccpi.optimisation.functions import MixedL21Norm, L2NormSquared, BlockFunction, L1Norm, KullbackLeibler, ZeroFunction                 
from ccpi.framework import TestData
import os
import sys

# user supplied input
if len(sys.argv) > 1:
    which_noise = int(sys.argv[1])
else:
    which_noise = 2
print ("Applying {} noise")

if len(sys.argv) > 2:
    method = sys.argv[2]
else:
    method = '0'
print ("method ", method)

loader = TestData(data_dir=os.path.join(sys.prefix, 'share','ccpi'))
data = loader.load(TestData.PEPPERS, size=(256,256))
ig = data.geometry
ag = ig

# Create noisy data. 
noises = ['gaussian', 'poisson', 's&p']
noise = noises[which_noise]
if noise == 's&p':
    n1 = TestData.random_noise(data.as_array(), mode = noise, salt_vs_pepper = 0.9, amount=0.2)
elif noise == 'poisson':
    scale = 5
    n1 = TestData.random_noise( data.as_array()/scale, mode = noise, seed = 10)*scale
elif noise == 'gaussian':
    n1 = TestData.random_noise(data.as_array(), mode = noise, seed = 10)
else:
    raise ValueError('Unsupported Noise ', noise)
noisy_data = ig.allocate()
noisy_data.fill(n1)


# Show Ground Truth and Noisy Data
plt.figure(figsize=(10,5))
plt.subplot(1,2,1)
plt.imshow(data.as_array())
plt.title('Ground Truth')
plt.colorbar()
plt.subplot(1,2,2)
plt.imshow(noisy_data.as_array())
plt.title('Noisy Data')
plt.colorbar()
plt.show()

# Regularisation Parameter depending on the noise distribution
if noise == 's&p':
    alpha = 1
elif noise == 'poisson':
    alpha = 0.15
elif noise == 'gaussian':
    alpha = 0.1

beta = 2 * alpha

# Fidelity
if noise == 's&p':
    f3 = L1Norm(noisy_data)
elif noise == 'poisson':
    f3 = KullbackLeibler(noisy_data)
elif noise == 'gaussian':
    f3 = 0.5 * L2NormSquared(noisy_data)

if method == '0':
    
    # Create operators
    op11 = Gradient(ig)
    op12 = Identity(op11.range_geometry())
    
    op22 = SymmetrizedGradient(op11.range_geometry())    
    op21 = ZeroOperator(ig, op22.range_geometry())
        
    op31 = Identity(ig, ag)
    op32 = ZeroOperator(op22.domain_geometry(), ag)
    
    operator = BlockOperator(op11, -1*op12, op21, op22, op31, op32, shape=(3,2) ) 
        
    f1 = alpha * MixedL21Norm()
    f2 = beta * MixedL21Norm() 
    
    f = BlockFunction(f1, f2, f3)         
    g = ZeroFunction()
        
else:
    
    # Create operators
    op11 = Gradient(ig)
    op12 = Identity(op11.range_geometry())
    op22 = SymmetrizedGradient(op11.range_geometry())    
    op21 = ZeroOperator(ig, op22.range_geometry())    
    
    operator = BlockOperator(op11, -1*op12, op21, op22, shape=(2,2) )      
    
    f1 = alpha * MixedL21Norm()
    f2 = beta * MixedL21Norm()     
    
    f = BlockFunction(f1, f2)         
    g = BlockFunction(f3, ZeroFunction())
     
# Compute operator Norm
normK = operator.norm()

# Primal & dual stepsizes
sigma = 1
tau = 1/(sigma*normK**2)

# Setup and run the PDHG algorithm
pdhg = PDHG(f=f,g=g,operator=operator, tau=tau, sigma=sigma)
pdhg.max_iteration = 500
pdhg.update_objective_interval = 500
pdhg.run(500)


#%%
# Show results
plt.figure(figsize=(20,5))
plt.subplot(1,3,1)
plt.imshow(data.as_array())
plt.title('Ground Truth')
plt.colorbar()
plt.subplot(1,3,2)
plt.imshow(noisy_data.as_array())
plt.title('Noisy Data')
plt.colorbar()
plt.subplot(1,3,3)
plt.imshow(pdhg.get_output()[0].as_array())
plt.title('TGV Reconstruction')
plt.colorbar()
plt.show()
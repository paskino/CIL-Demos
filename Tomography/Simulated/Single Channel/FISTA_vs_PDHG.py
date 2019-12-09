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
Compare solutions of FISTA & PDHG algorithms


Problem:     min_x alpha * ||\grad x ||^{2}_{2} + || x - g ||_{1}

             \alpha: Regularization parameter
             
             \nabla: Gradient operator
             
             g: Noisy Data with Salt & Pepper Noise

"""

from ccpi.framework import ImageData, ImageGeometry, TestData

import numpy as np 
import numpy                          
import matplotlib.pyplot as plt

from ccpi.optimisation.algorithms import FISTA, PDHG

from ccpi.optimisation.operators import BlockOperator, Gradient, Identity
from ccpi.optimisation.functions import L2NormSquared, L1Norm, \
                                         FunctionOperatorComposition, BlockFunction, ZeroFunction
                                                
# Create Ground truth and Noisy data
N = 100

data = np.zeros((N,N))
data[round(N/4):round(3*N/4),round(N/4):round(3*N/4)] = 0.5
data[round(N/8):round(7*N/8),round(3*N/8):round(5*N/8)] = 1
data = ImageData(data)
ig = ImageGeometry(voxel_num_x = N, voxel_num_y = N)
ag = ig

n1 = TestData.random_noise(data.as_array(), mode = 's&p', salt_vs_pepper = 0.9, amount=0.2)
noisy_data = ImageData(n1)

# Regularisation Parameter
alpha = 5

###############################################################################
# Setup and run the FISTA algorithm
operator = Gradient(ig)
fidelity = L1Norm(b=noisy_data)
regulariser = FunctionOperatorComposition(alpha * L2NormSquared(), operator)

x_init = ig.allocate()
opt = {'memopt':True}
fista = FISTA(x_init=x_init , f=regulariser, g=fidelity, opt=opt)
fista.max_iteration = 2000
fista.update_objective_interval = 50
fista.run(2000, verbose=False)
###############################################################################


###############################################################################
# Setup and run the PDHG algorithm
op1 = Gradient(ig)
op2 = Identity(ig, ag)

operator = BlockOperator(op1, op2, shape=(2,1) )   
f = BlockFunction(alpha * L2NormSquared(), fidelity)                                        
g = ZeroFunction()
  
normK = operator.norm()

sigma = 1
tau = 1/(sigma*normK**2)

pdhg = PDHG(f=f,g=g,operator=operator, tau=tau, sigma=sigma, memopt=True)
pdhg.max_iteration = 2000
pdhg.update_objective_interval = 200
pdhg.run(2000, verbose=False)
###############################################################################

# Show results

plt.figure(figsize=(10,10))

plt.subplot(2,1,1)
plt.imshow(pdhg.get_output().as_array())
plt.title('PDHG reconstruction')

plt.subplot(2,1,2)
plt.imshow(fista.get_output().as_array())
plt.title('FISTA reconstruction')

plt.show()

diff1 = pdhg.get_output() - fista.get_output()

plt.imshow(diff1.abs().as_array())
plt.title('Diff PDHG vs FISTA')
plt.colorbar()
plt.show()



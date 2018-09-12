"""
Produce the interpolation which corresponds to Figure 2 of the article
"""

import os

# Mathematical functions
import numpy as np
import scipy.sparse as scsp
import scipy.sparse.linalg as scspl
from numpy import linalg as lin

from math import *

# Import the useful routines
import read_off
import surface_pre_computations
import geodesic_surface_congested
import cut_off

# To plot graph
import matplotlib.pyplot as plt

# To plot triangulated surfaces
from mayavi import mlab
from mayavi.api import Engine


engine = Engine()
engine.start()



# -----------------------------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------------------------

# Discretization of the starting [0,1] (for the centered grid)
nTime = 31

# Name of the file in which is stored the triangulated surface D
nameFileD = os.path.join("meshes", "face_vector_field_319.off")

# Parameter epsilon to regularize the Laplace problem
eps = 0.0*10**(-8)

# Number of iterations
Nit = 1000

# Detailed Study: True if we compute the objective functional at every time step (slow), False in the case we compute every 10 iterations.
detailStudy = False

# Value for the congestion parameter (alpha in the article)
cCongestion = 0.1

# -----------------------------------------------------------------------------------------------
# Read the .off file
# -----------------------------------------------------------------------------------------------

# Extract Vertices, Triangles, Edges
Vertices, Triangles, Edges = read_off.readOff(nameFileD)

# Compute areas of Triangles
areaTriangles, angleTriangles, baseFunction	 = surface_pre_computations.geometricQuantities(Vertices, Triangles, Edges)

# Compute the areas of the Vertices
originTriangles, areaVertices, vertexTriangles = surface_pre_computations.trianglesToVertices( Vertices,Triangles, areaTriangles)

# -----------------------------------------------------------------------------------------------
# Define the boundary conditions
# -----------------------------------------------------------------------------------------------

nVertices = Vertices.shape[0]

mub0 = np.zeros(nVertices)
mub1 = np.zeros(nVertices)

lengthScale = 0.1

# Center of the "blobs" for mub0 and mub1
center0 = Vertices[4492,:]
center1 = Vertices[4225,:]

for i in range(nVertices) :

	# Change of coordinates
	alpha = 0.1 * Vertices[i,0] + Vertices[i,1]
	beta = - Vertices[i,0] + 0.1 * Vertices[i,1]
	gamma = Vertices[i,2]

	# Define mub0
	if gamma >= -0.1 :
		mub0[i] = areaVertices[i] * cut_off.f(-0.2-alpha,0.3) * cut_off.f(alpha - 0.15,0.3) * cut_off.f(0.1 - beta,0.3) * cut_off.f(beta - 0.45,0.3)

	# Define mub1
	mub1[i] += areaVertices[i] * exp( -lin.norm( Vertices[i,:] - center0  )**2 / lengthScale**2  )
	mub1[i] += areaVertices[i] * exp( -lin.norm( Vertices[i,:] - center1  )**2 / lengthScale**2  )

# Normalization
mub0 /= np.sum(mub0)
mub1 /= np.sum(mub1)

# -----------------------------------------------------------------------------------------------
# Call the algorithm
# -----------------------------------------------------------------------------------------------

phi,mu,A,E,B,objectiveValue,primalResidual,dualResidual = geodesic_surface_congested.geodesic( nTime, nameFileD, mub0,mub1, cCongestion,eps, Nit, detailStudy )

# Plot the primal and dual residuals to check that everything is ok

plt.semilogy(primalResidual, label = "Primal residual")
plt.semilogy(dualResidual, label = "Dual residual")

plt.title("Primal and dual Residuals")

plt.legend()
plt.show()

# -----------------------------------------------------------------------------------------------
# Saving the results
# -----------------------------------------------------------------------------------------------

np.savetxt("face_mu_store.txt", mu.reshape((nTime*nVertices)) )

# -----------------------------------------------------------------------------------------------
# Printing the results with mayavi
# -----------------------------------------------------------------------------------------------

# Parameter for the mayavi scene of this example

def parametersMayavi(scene) :

	# Put the right angle
	scene.scene.camera.position = [-0.069944662502985533, 1.2526435392885236, 3.9345675528530402]
	scene.scene.camera.focal_point = [0.0052490000000000037, 0.06885150000000001, 0.033782499999999993]
	scene.scene.camera.view_angle = 30.0
	scene.scene.camera.view_up = [0.99362963464680065, -0.10108021570105792, 0.049829099384727987]
	scene.scene.camera.clipping_range = [2.5610091024871435, 6.0229878620594661]
	scene.scene.camera.compute_view_plane_normal()
	scene.scene.render()

	# Background color
	scene.scene.background = (1.0, 1.0, 1.0)

for i in [0,(nTime-1) // 4,  (nTime-1) // 2, (3*nTime-1) // 4, nTime-1] :

	# What we want to plot is the density
	muNormalized = np.divide(mu[i,:], areaVertices)

	# The normalization of the color map is done independently for each instant
	toPlot = (np.max(muNormalized) - muNormalized) / np.max(muNormalized)

	mlab.triangular_mesh(Vertices[:,0], Vertices[:,1], Vertices[:,2], Triangles, scalars=toPlot, colormap = "bone")

	parametersMayavi(engine.scenes[0])

	# Uncomment to save the figure
	# mlab.savefig("face_mu_" + str(i)+ ".png", size = (300,500))
	# mlab.close()

	mlab.show()

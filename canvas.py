import numpy as np
from CSG import *

def compute_distance(grid, states, y, x, h, maxdist = np.inf, debug_map=None):
    #find the upwind values along each dimension
    mindists = [maxdist, maxdist]
    for dim in [0,1]:
        for dist in [-1,1]:
            coords = [y,x]
            coords[dim] += dist
            py, px = coords
            if coords[dim] < 0 or coords[dim] >= grid.shape[dim]:
                continue
            if states[py, px] == 0:
                continue
            mindists[dim] = min(mindists[dim], grid[py, px])
    Uy, Ux = mindists
    if Uy < maxdist and Ux < maxdist:
        disc = 2*h*h - (Ux - Uy)**2
        if disc >= 0:
            dist = 0.5*(Uy+Ux)+0.5*np.sqrt(disc)
            return dist

    #fall back on one-sided update if quadratic has no roots
    Umin = min(Ux, Uy)
    if Umin >= maxdist:
        return maxdist

    return h+Umin


def partialy(x):
    x2 = np.roll(x,-1, 0)
    x1 = np.roll(x, 1, 0)
    result = np.zeros(x.shape)
    result[0,:] = x2[0,:] - x[0,:]
    result[-1,:] = x[-1,:] - x1[-1,:]
    result[1:-1,:] = (x2[1:-1,:] - x1[1:-1,:])*0.5
    return result
def partialx(x):
    x2 = np.roll(x,-1, 1)
    x1 = np.roll(x, 1, 1)
    result = np.zeros(x.shape)
    result[:,0] = x2[:,0] - x[:,0]
    result[:,-1] = x[:,-1] - x1[:,-1]
    result[:,1:-1] = (x2[:,1:-1] - x1[:,1:-1])*0.5
    return result


class Canvas:
    def __init__(self, dims=[10, 10], spacing=1, maxdist = 1):
        self.dims = np.array(dims, dtype=np.float)
        self.resolution = np.ceil(self.dims / spacing).astype(np.int)
        self.grid = np.full(self.resolution, maxdist)
        self.indices = np.indices(self.resolution)
        self.coords = self.indices.astype(np.float) * spacing
        self.normals = np.full((2, self.resolution[0], self.resolution[1]), np.nan)
        self.spacing = spacing
        self.maxdist = maxdist

    def clear(self):
        self.grid.fill(self.maxdist)
        self.normals.fill(np.nan)

    def draw_solid(self, shape, subtract=False):
        vals = np.apply_along_axis(shape, 0, self.coords)
        if subtract:
            self.grid = np.maximum(self.grid, -vals)
        else:
            self.grid = np.minimum(self.grid, vals)

    def displace(self, distance):
        self.grid -= distance
        #self.update() #needed in the event of non-uniform displacement only, I think

    def update(self):
        self.update_sdf()
        self.update_normals()

    def update_normals(self):
        self.normals = np.stack([partialy(self.grid), partialx(self.grid)]) / self.spacing

    def fast_marching(self, clear=True, debug_map=None):
        #fast marching algorithm by sethian
        #states:
        #0 = far
        #1 = considered
        #2 = accepted

        #initialization
        L = set()
        states = np.zeros_like(self.grid, np.int)
        states[self.grid <= 0] = 2
        if clear:
            self.grid[states != 2] = self.maxdist
        mask = states == 2
        mask2 = (mask + sum([sum([np.roll(mask, dir, dim) for dir in [-1,1]]) for dim in [0,1]])) != 0
        mask = mask2 ^ mask #initial set of nodes added to L: neighbor set of accepted nodes
        states[mask] = 1
        inds = self.indices[:,mask]
        for i in range(inds.shape[1]):
            y, x = inds[:,i]
            u = compute_distance(self.grid, states, y, x, self.spacing, maxdist = self.maxdist, debug_map=debug_map)
            if u < self.grid[y,x]:
                self.grid[y,x] = u
            L.add((y, x))

        #main loop
        while len(L) > 0:
            y, x = min(L, key=lambda yx:self.grid[yx[0],yx[1]])
            states[y,x] = 2
            L.remove((y,x))
            for dim in [0, 1]:
                for direction in [-1,1]:
                    coords = [y, x]
                    coords[dim] = min(max(0, coords[dim]+direction), states.shape[dim]-1)
                    py, px = coords
                    if states[py, px] != 2:
                        u = compute_distance(self.grid, states, py, px, self.spacing, maxdist = self.maxdist, debug_map=debug_map)
                        if u < self.grid[py,px]:
                            self.grid[py,px] = u
                        if u < self.maxdist and states[py, px] == 0:
                            states[py, px] = 1
                            L.add((py,px))

    def update_sdf(self, clear=True, debug_map=None):
        self.fast_marching(clear=clear, debug_map=debug_map)
        self.grid = -self.grid
        self.fast_marching(clear=clear, debug_map=debug_map)
        self.grid = -self.grid

def display_normals(normals, mask):
    normals = np.insert(normals / 3 + 0.5, 0, 0.5, axis=0)
    plt.imshow((normals * mask.reshape(1,*mask.shape)).transpose((1, 2, 0)), origin='lower')
    plt.show()

def show_update(can):
    X = can.coords[1,0,:]
    Y = can.coords[0,:,0]
    mask = np.abs(can.grid) < 0.1
    can.update_normals()
    display_normals(can.normals, mask)
    plt.imshow(can.grid, extent=(X[0],X[-1],Y[0],Y[-1]), origin='lower')
    CL = plt.contour(X, Y, can.grid, levels=contours)
    plt.clabel(CL)
    plt.show()
    t1 = time()
    can.update_sdf(debug_map=debug_map)
    print('updated in: {}'.format(time() - t1))
    can.update_normals()
    plt.imshow(can.grid, extent=(X[0],X[-1],Y[0],Y[-1]), origin='lower')
    CL = plt.contour(X, Y, can.grid, levels=contours)
    plt.clabel(CL)
    plt.show()
    #plt.contour(can.grid, levels=contours)
    #plt.imshow(np.sqrt(can.normals[0]*can.normals[0] + can.normals[1]*can.normals[1]))
    #plt.colorbar()
    plt.show()

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from time import time
    can = Canvas([10,10], 0.1, maxdist=2)
    debug_map = np.zeros_like(can.grid, dtype=np.int)
    contours = np.linspace(-2, 2, 11)

    square = Square(1.5)
    square.set_translation([5, 5])

    square2 = Square(1.3)
    square2.set_rotation(np.pi/4)
    square2.set_translation([6,6])

    squares = Intersection(square, Negation(square2))

    can.draw_solid(squares)
    show_update(can)
    can.displace(1.6)
    display_normals(can.normals, np.abs(can.grid) < 0.1)
    can.clear()

    circle = Circle(3.5)
    circle.set_translation([4,5])
    circle2 = Circle(2)
    circle2.set_translation([7.4,7.4])
    circles = Union(circle, circle2)
    can.draw_solid(circles)
    show_update(can)
    can.displace(-1.6)
    display_normals(can.normals, np.abs(can.grid) < 0.1)

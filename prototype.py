import numpy as np

def compute_distance(grid, states, y, x, h, debug_map=None):
    mindists = [np.inf, np.inf]
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
    if np.isfinite(Uy) and np.isfinite(Ux):
        disc = 2*h*h - (Ux - Uy)**2
        if disc >= 0:
            dist = 0.5*(Uy+Ux)+0.5*np.sqrt(disc)
            return dist
    #fall back on one-sided update if quadratic has no roots
    dist = np.inf
    for Ui in mindists:
        if np.isfinite(Ui):
            dist = min(dist, h + Ui)

    if np.isfinite(dist):
        return dist
        
    print('failed to find distance')
    if debug_map is not None:
        debug_map[y,x] = 1
    return np.inf




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
    def __init__(self, dims=[10, 10], resolution=[100,100]):
        self.dims = np.array(dims, dtype=np.float)
        self.resolution = np.array(resolution, dtype=np.float)
        self.grid = np.full(resolution, np.inf)
        self.indices = np.indices(resolution)
        self.spacing = self.dims/self.resolution
        self.coords = self.indices * self.spacing.reshape(2, 1, 1)
        self.normals = np.full((2, resolution[0], resolution[1]), np.nan)

    def clear(self):
        self.grid.fill(np.inf)
        self.normals.fill(0)

    def draw_circle(self, pos, radius=1, subtract=False):
        pos = np.array(pos)
        circle = np.sqrt(np.sum((self.coords - pos.reshape(2, 1, 1))**2, 0)) - radius

        if subtract:
            self.grid = np.maximum(self.grid, -circle)
        else:
            self.grid = np.minimum(self.grid, circle)

        self.update()

    def draw_square(self, center, radius, angle=0, subtract=False):
        rotmat = np.array([[np.cos(angle), -np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        rotcoords = np.dot(rotmat, self.coords.transpose((1, 0, 2)))
        center = rotmat.dot(np.array(center))
        rotcoords -= center.reshape(2, 1, 1)
        rect = np.maximum(*[np.maximum(-radius - rotcoords[dim], rotcoords[dim] - radius) for dim in [0, 1]])
        if subtract:
            self.grid = np.maximum(self.grid, -rect)
        else:
            self.grid = np.minimum(self.grid, rect)

        self.update()

    def displace(self, distance):
        self.grid -= distance
        self.update() #needed in the event of non-uniform displacement only, I think

    def update(self):
        #self.update_sdf()
        self.update_normals()

    def update_normals(self):
        self.normals = np.stack([partialy(self.grid), partialx(self.grid)]) / self.spacing.reshape(2, 1, 1)

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
            self.grid[states != 2] = np.inf
        mask = states == 2
        mask2 = (mask + sum([sum([np.roll(mask, dir, dim) for dir in [-1,1]]) for dim in [0,1]])) != 0
        mask = mask2 ^ mask #initial set of nodes added to L
        states[mask] = 1
        inds = self.indices[:,mask]
        for i in range(inds.shape[1]):
            y, x = inds[:,i]
            u = compute_distance(self.grid, states, y, x, self.spacing[0], debug_map) #TODO: enforce consistent x and y spacing
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
                        u = compute_distance(self.grid, states, py, px, self.spacing[0], debug_map)
                        if u < self.grid[py,px]:
                            self.grid[py,px] = u
                        if states[py, px] == 0:
                            states[py, px] = 1
                            L.add((py,px))

    def update_sdf(self, clear=True, debug_map=None):
        self.fast_marching(clear=clear, debug_map=debug_map)
        self.grid = -self.grid
        self.fast_marching(clear=clear, debug_map=debug_map)
        self.grid = -self.grid

def display_normals(normals, mask):
    normals = np.insert(normals / 3 + 0.5, 0, 0.5, axis=0)
    plt.imshow((normals * mask.reshape(1,*mask.shape)).transpose((1, 2, 0)))
    plt.show()

def show_update(can):
    mask = np.abs(can.grid) < 0.1
    display_normals(can.normals, mask)
    plt.imshow(can.grid)
    CL = plt.contour(can.grid, levels=contours)
    plt.clabel(CL)
    plt.show()
    can.update_sdf(debug_map=debug_map)
    plt.imshow(can.grid)
    CL = plt.contour(can.grid, levels=contours)
    plt.clabel(CL)
    plt.show()
    plt.contour(can.grid, levels=contours)
    plt.imshow(np.sqrt(can.normals[0]*can.normals[0] + can.normals[1]*can.normals[1]))
    plt.colorbar()
    plt.show()

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    can = Canvas([10,10], [100,100])
    debug_map = np.zeros_like(can.grid, dtype=np.int)
    contours = np.linspace(-2, 2, 11)

    can.draw_square([5,5],radius=1.5, angle=np.pi/8)
    show_update(can)

    can.clear()
    can.draw_circle([5, 5], radius=1)
    show_update(can)

    can.clear()

    can.draw_circle([4,5], radius=3.5)
    can.draw_circle([7.4,7.4], radius=2, subtract=False)
    show_update(can)

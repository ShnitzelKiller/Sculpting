import numpy as np

def compute_distance(grid, states, y, x, h):
    quadrants = []
    for py in [y-1,y+1]:
        if py < 0 or py >= grid.shape[0]:
            continue
        for px in [x-1,x+1]:
            if px < 0 or px >= grid.shape[1]:
                continue
            if states[py, x] == 0 or states[y, px] == 0:
                continue
            Uy = grid[py,x]
            Ux = grid[y, px]
            if not np.isfinite(Uy) or not np.isfinite(Ux):
                continue
            disc = (Uy+Ux)**2-2*(Uy*Uy+Ux*Ux-h*h)
            if disc < 0:
                continue
            dist = 0.5*(Uy+Ux)+0.5*np.sqrt(disc)
            quadrants.append(dist)
    #fall back on one-sided update if quadratic has no roots
    if len(quadrants) == 0:
        sides = []
        for dim in [0, 1]:
            for dist in [-1, 1]:
                coords = [y, x]
                coords[dim] += dist
                if coords[dim] < 0 or coords[dim] >= grid.shape[dim]:
                    continue
                py, px = coords
                if states[py, px] == 0:
                    continue
                Ui = grid[py, px]
                if not np.isfinite(Ui):
                    continue
                dist = h + Ui
                sides.append(dist)
        if len(sides) == 0:
            return np.inf
        else:
            return min(sides)

    else:
        return min(quadrants)

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

    def draw_circle(self, pos, radius=1, subtract=False):
        pos = np.array(pos)
        circle = np.sqrt(np.sum((self.coords - pos.reshape(2, 1, 1))**2, 0)) - radius

        if subtract:
            self.grid = np.maximum(self.grid, -circle)
        else:
            self.grid = np.minimum(self.grid, circle)

        self.update()

    def displace(self, distance):
        self.grid += distance
        self.update() #needed in the event of non-uniform displacement only, I think

    def update(self):
        #self.update_sdf()
        self.update_normals()

    def update_normals(self):
        self.normals = np.stack([partialy(self.grid), partialx(self.grid)]) * (self.resolution/self.dims).reshape(2, 1, 1)

    def update_sdf(self):
        #fast marching by sethian
        #states:
        #0 = far
        #1 = considered
        #2 = accepted
        L = set()
        states = np.zeros_like(self.grid, np.int)
        states[self.grid <= 0] = 2
        self.grid[states != 2] = np.inf
        mask = states == 2
        mask2 = (mask + sum([sum([np.roll(mask, dir, dim) for dir in [-1,1]]) for dim in [0,1]])) != 0
        mask = mask2 ^ mask #initial set of nodes added to L
        states[mask] = 1
        inds = self.indices[:,mask]
        for i in range(inds.shape[1]):
            y, x = inds[:,i]
            u = compute_distance(self.grid, states, y, x, self.spacing[0]) #TODO: enforce consistent x and y spacing
            if u < self.grid[y,x]:
                self.grid[y,x] = u
            L.add((y, x))

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
                        u = compute_distance(self.grid, states, py, px, self.spacing[0])
                        if u < self.grid[py,px]:
                            self.grid[py,px] = u
                        if states[py, px] == 0:
                            states[py, px] = 1
                            L.add((py,px))


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    can = Canvas([10,10], [100,100])
    can.draw_circle([4,5], radius=4)
    can.draw_circle([8,5], radius=2, subtract=False)

    mask = np.abs(can.grid) < 0.1
    plt.imshow(can.normals[0] * mask)
    plt.show()

    plt.imshow(can.grid)
    plt.show()
    can.update_sdf()
    can.grid = -can.grid
    can.update_sdf()
    can.grid = -can.grid
    plt.imshow(can.grid)
    plt.show()

    can.displace(1)
    mask = np.abs(can.grid) < 0.1
    plt.imshow(can.normals[0] * mask)
    plt.show()
    can.displace(-1)
    mask = np.abs(can.grid) < 0.1
    plt.imshow(can.normals[0] * mask)
    plt.show()

import numpy as np

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
        self.inds = np.indices(resolution) * (self.dims/self.resolution).reshape(2, 1, 1)
        self.normals = np.full((2, resolution[0], resolution[1]), np.nan)

    def draw_circle(self, pos, radius=1, subtract=False):
        pos = np.array(pos)
        circle = np.sqrt(np.sum((self.inds - pos.reshape(2, 1, 1))**2, 0)) - radius

        if subtract:
            self.grid = np.maximum(self.grid, -circle)
        else:
            self.grid = np.minimum(self.grid, circle)

        self.update()

    def update(self):
        self.update_sdf()
        self.update_normals()

    def update_normals(self):
        self.normals = np.stack([partialy(self.grid), partialx(self.grid)]) * (self.resolution/self.dims).reshape(2, 1, 1)

    def update_sdf(self):
        print('not implemented')


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    can = Canvas([10,10], [100,100])
    can.draw_circle([4,5], radius=4)
    can.draw_circle([8,5], radius=2)

    mask = np.abs(can.grid) < 0.2
    plt.imshow(can.normals[0] * mask)
    plt.show()
    plt.imshow(can.normals[1] * mask)
    plt.show()

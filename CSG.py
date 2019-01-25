class CSG(object):
    def __init__(self):
        self.rotation = np.eye(2)
        self.translation = np.zeros(2)
    def __call__(self, pos):
        if not hasattr(self, '_map'):
            raise ValueError('CSG solid does not implement map function')
        return self._map(self._transform(pos))
    def _transform(self, pos):
        return self.rotation.dot(pos - self.translation)
    def set_rotation(self, angle):
        c = np.cos(-angle)
        s = np.sin(-angle)
        self.rotation = np.array([[c, -s], [s, c]])
    def set_translation(self, offset):
        self.translation = np.array(offset)

class Union(CSG):
    def __init__(self, *shapes):
        super(Union, self).__init__()
        self.shapes = shapes
    def _map(self, pos):
        return min([shape(pos) for shape in self.shapes])

class Intersection(CSG):
    def __init__(self, *shapes):
        super(Intersection, self).__init__()
        self.shapes = shapes
    def _map(self, pos):
        return max([shape(pos) for shape in self.shapes])

class Negation(CSG):
    def __init__(self, shape):
        super(Negation, self).__init__()
        self.shape = shape
    def _map(self, pos):
        return -self.shape(pos)

class Circle(CSG):
    def __init__(self, radius):
        super(Circle, self).__init__()
        self.radius = radius
    def _map(self, pos):
        return np.sqrt(pos[0]*pos[0]+pos[1]*pos[1]) - self.radius

class Square(CSG):
    def __init__(self, radius):
        super(Square, self).__init__()
        self.radius = radius
    def _map(self, pos):
        inside = np.max(np.abs(pos)) - self.radius
        disp = np.clip(np.abs(pos)-self.radius, 0, None)
        return min(inside, 0) + np.sqrt(disp.dot(disp))

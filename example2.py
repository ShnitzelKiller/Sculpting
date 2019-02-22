from frontend import *

def getCmds():
	shape = UniformSolid(False)

	for n in range(5):
		scale = 1.0/(n+1)
		shape = Union(shape, Translate(Scale(Circle(), Vec2(scale,scale)), Vec2(0, n)))


	return Output(shape)

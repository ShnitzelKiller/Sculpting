from frontend import *
from numpy import sin, cos

def getCmds1():
	shape = UniformSolid(False)

	for n in range(5):
		scale = 1.0/(n+1)
		shape = Union(shape, Translate(Scale(Circle(), Vec2(scale,scale)), Vec2(0, n)))
	#shape2 = Scale(Square(), Vec2(0.2, 5))
	#field = SolidToField(shape2)
	#shape=ExpandSurface(shape, field, 0.2)

	return Output(shape)

def getCmds2():
	shape = Circle()
	num = 6
	for i in range(num):
		ang = i/num * 6.28
		cog = Scale(Circle(), Vec2(0.4, 0.4))
		shape = Union(shape, Translate(cog, Vec2(cos(ang), sin(ang))))
	field = UniformField(1)
	shape2 = ExpandSurface(shape, field, -0.2)
	return Output(shape2)

def getCmds3():
	shape = Circle()
	shape2 = Translate(Circle(), Vec2(0.2, 0))
	shape3 = Subtract(shape, shape2)
	return Output(shape3)

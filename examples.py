from frontend import *
from numpy import sin, cos

def getCmds1():
	shape = UniformSolid(False)

	for n in range(5):
		scale = 1.0/(n+1)
		shape = Union(shape, Translate(Scale(Circle(), Vec2(scale,scale)), Vec2(0, n)))
	shape2 = Scale(Square(), Vec2(0.2, 5))
	shape2 = Union(shape2, shape)
	#field = SolidToField(shape2)
	#shape=ExpandSurface(shape, field, 0.2)

	return Output(shape2)

def replicate(branch, thickness=0.2, vee=Translate(Scale(Square(), Vec2(0.2, 1)), Vec2(0, -1))):
	piece = Union(vee, Translate(branch, Vec2(0, -2)))
	left = Rotate(piece, 30)
	right = Rotate(piece, -30)
	return Union(left, right, Scale(Circle(), Vec2(thickness, thickness)))

def getCmds2():
	shape = Circle()
	num = 12
	for i in range(num):
		ang = i/num * 6.28
		cog = Scale(Circle(), Vec2(0.4, 0.4))
		shape = Union(shape, Translate(cog, Vec2(cos(ang), sin(ang))))
	field = UniformField(1)
	shape2 = ExpandSurface(shape, field, -0.2)
	shape2 = Scale(shape2, Vec2(0.75, 0.75))
	vee = Translate(Scale(Square(), Vec2(0.2, 1)), Vec2(0, -1))
	piece = Union(vee, Translate(shape2, Vec2(0, -2)))
	left = Rotate(piece, 30)
	right = Rotate(piece, -30)
	shape3 = Union(left, right, Scale(Circle(), Vec2(0.3, 0.3)))
	return Output(shape3)

def getCmds3():
	shape = Circle()
	shape2 = Translate(Circle(), Vec2(0.2, 0))
	shape3 = Subtract(shape, shape2)
	return Output(shape3)

def getCmds4():
	thickness = 0.4
	vee = Translate(Scale(Square(), Vec2(thickness, 1)), Vec2(0, -1))
	tree = replicate(Scale(Circle(), Vec2(0.75, 0.75)), thickness, vee)
	fac = 0.75
	f = UniformField(1)
	for i in range(4):
		tree = replicate(Scale(tree, Vec2(1, fac)), thickness, vee)
		tree = ExpandSurface(tree, f, -0.05)

	return Output(tree)

def getCmds5(): #tree for testing performance difference (no surface ops)
	thickness = 0.4
	vee = Translate(Scale(Square(), Vec2(thickness, 1)), Vec2(0, -1))
	tree = replicate(Scale(Circle(), Vec2(0.75, 0.75)), thickness, vee)
	fac = 0.75
	for i in range(6):
		tree = replicate(Scale(tree, Vec2(fac, fac)), thickness, vee)

	return Output(tree)

def getCmds6():
	shape = Circle()
	shape2 = Translate(Circle(), Vec2(1, 0))
	field = SolidToField(shape2, 0.5)
	finalshape = ExpandSurface(shape, field, -0.5)
	return Output(finalshape)

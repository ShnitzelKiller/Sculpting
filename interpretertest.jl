using PyCall

ex = pyimport("examples")

cmds = ex[:getCmds1]()

include("interpreter.jl")

result = execute(cmds)

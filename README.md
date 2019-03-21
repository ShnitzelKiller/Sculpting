# 2D Sculpting

![tree](tree.PNG)
![Abstract mushroom](step5.jpg)


## Running Examples
To run a few examples (which will be saved as example*.png in this directory), run
```
julia interpretertest.jl
```
This runs the interpreter in `interpreter.jl` on a couple of the tests defined in `examples.py`.
This processes the input AST in the script `frontend.py` to produce the intermediate representation, which is then interpreted by `interpreter.jl`.

This assumes you have Julia installed, with the packages DataStructures, Plots, Images, and PyCall installed. To install a package, within the Julia command prompt execute:
```
using Pkg
Pkg.add(“PackageName”)
```
Note that runtimes sometimes appear to be long, but the vast majority of the time is spent loading packages. Julia is not meant to be reloaded for individual small tasks. However, the backend algorithms themselves are orders of magnitude faster than their python counterparts.

The frontend python code used to generate the image is in examples.py (each getCmds() function is a separate example) and the code is compiled and run using interpretertest.jl in Julia.


## File structure
### Frontend
A frontend that optimizes the intermediate representation is found in `frontend.py`, and an example programs are located in `examples.py`.

### Backend
The primitive operations on shapes are defined in `CSG.jl`, while the code pertaining to discretization is located in `canvas.jl`, and the algorithms for computing SDF values are located in `fast_marching.jl`. `selectors.jl` contains definitions of field objects, along with code for discretizing and sampling fields. Some additional math functions are defined in `mathutil.jl`.

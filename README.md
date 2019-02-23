# 2D Sculpting


# Milestone III: Partial interpreter implementation
The interpreter can be run on the test described in the document by running `julia interpretertest.jl`.
This assumes you have Julia installed, with the packages DataStructures, Plots, Images installed. To install a package, within the Julia command prompt execute:
```
using Pkg
Pkg.add(“PackageName”)
```
Then the above script should produce the same image as in the example in the document (albeit rotated since it fit better in the document that way).


## Sculpting prototype
To see the results of the python implementation, run
```
python canvas.py
```
There will be a series of plots, each showing steps in the construction of various shapes (CSG operations followed by signed distance field updates, then shrinking and fattening).

To run the Julia tests, install IJulia with
```
Pkg.add("IJulia")
using IJulia
notebook()
```
in the Julia REPL. Then you can run `include("canvas.jl")` in a new notebook, or see the existing notebook in this directory.
Here is an example of the output of the sculpting prototype system:
![Abstract mushroom](step5.jpg)

## DSL code
A frontend that optimizes the intermediate representation is found in `frontend.py`, and an example program using this frontend is in `example.py`.

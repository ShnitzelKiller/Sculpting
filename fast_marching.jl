using DataStructures

function compute_distance(grid::Matrix{T}, I::CartesianIndex{2}, Ifirst::CartesianIndex{2}, Ilast::CartesianIndex{2}, h::Real, maxdist::Real) where {T <: AbstractFloat}
    Iv = CartesianIndex(1, 0)
    Ih = CartesianIndex(0, 1)

    function m(Ii)
        Jfirst = max(I-Ii, Ifirst)
        Ufirst = Jfirst == I ? maxdist : grid[Jfirst]
        Jlast = min(I+Ii, Ilast)
        Ulast = Jlast == I ? maxdist : grid[Jlast]
        return min(Ufirst, Ulast)
    end
    Uh, Uv = m(Ih), m(Iv)
    # if !isfinite(Uv)
    #     Jfirst = max(I-Iv, Ifirst)
    #     print("Jfirst: $Jfirst")
    #     Ufirst = Jfirst == I ? maxdist : grid[Jfirst]
    #     print("Ufirst: $Ufirst")
    #     Jlast = min(I+Iv, Ilast)
    #     print("Jlast: $Jlast")
    #     Ulast = Jlast == I ? maxdist : grid[Jlast]
    #     print("Ulast: $Ulast")
    # end
    if Uh < maxdist && Uv < maxdist
        disc = 2*h^2-(Uh-Uv)^2
        if disc >= 0
            return min((Uh+Uv)/2+sqrt(disc)/2, maxdist)
        end
    end

    Umin = min(Uv, Uh)
    return min(h+Umin, maxdist)
end
function fast_marching!(states::Matrix{UInt8}, grid::Matrix{T}, h::T, maxdist::T) where {T <: AbstractFloat}
    L = PriorityQueue{CartesianIndex{2}, T}()
    R = CartesianIndices(grid)
    Ifirst, Ilast = first(R), last(R)
    Iv = CartesianIndex(1, 0)
    Ih = CartesianIndex(0, 1)

    for I in R
        if states[I] == 0
            if (states[max(Ifirst, I-Iv)] >= 2 ||
             states[max(Ifirst, I-Ih)] >= 2 ||
             states[min(Ilast, I+Ih)] >= 2 ||
             states[min(Ilast, I+Iv)] >= 2)
                states[I] = 1
                dist = compute_distance(grid, I, Ifirst, Ilast, h, maxdist)
                grid[I] = dist

                enqueue!(L, I, dist)
            end
        end
    end
    
    #main loop
    while !isempty(L)
        I = dequeue!(L)
        states[I] = 2
        for Ii = (Iv, Ih)
            for J = (min(I+Ii, Ilast), max(I-Ii, Ifirst))
                if states[J] < 2
                    dist = compute_distance(grid, J, Ifirst, Ilast, h, maxdist)
                    if dist < grid[J]
                        grid[J] = dist
                        if states[J] == 1
                            L[J] = dist
                        else
                            states[J] = 1
                            enqueue!(L, J, dist)
                        end
                    end
                end
            end
        end
    end
    return nothing
end
function fast_marching!(grid::Matrix{T}, h::Real, maxdist::Real=1) where {T <: AbstractFloat}
    h, maxdist = convert(T, h), convert(T, maxdist)
    states = zeros(UInt8, size(grid))::Matrix{UInt8}
    for i in eachindex(grid)
        if grid[i] <= 0
            states[i] = 3
            grid[i] = 0 #TODO: find a way to keep these estimates intact
        else
            grid[i] = maxdist
        end
    end
    fast_marching!(states, grid, h, maxdist)
    for i in eachindex(grid)
        if states[i] == 3
            states[i] = 0
            grid[i] = maxdist
        else
            states[i] = 3
            grid[i] = -grid[i]
        end
    end
    fast_marching!(states, grid, h, maxdist)
    for i in eachindex(grid)
        grid[i] = -grid[i]
    end
    return states #TODO: remove
end

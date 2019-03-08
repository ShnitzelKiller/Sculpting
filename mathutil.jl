function interpolate(mat::Matrix{T}, posy::T, posx::T, default::T=typemax(T)) where {T}
    h, w = size(mat)
    if posx >= w-1 || posx < 0 || posy >= h-1 || posy < 0
        return default
    else
        x0 = Int(floor(posx))+1
        y0 = Int(floor(posy))+1
        x1 = x0 + 1
        y1 = y0 + 1
        xfac = posx - (x0-1)
        yfac = posy - (y0-1)
        v00 = mat[y0,x0]
        v01 = mat[y0,x1]
        v10 = mat[y1,x0]
        v11 = mat[y1,x1]
        xavg0 = (1-xfac)*v00 + xfac*v01
        xavg1 = (1-xfac)*v10 + xfac*v11
        return (1-yfac)*xavg0 + yfac*xavg1
    end
end

function partial!(B, A, dims...)
    R = CartesianIndices(A)
    Ifirst, Ilast = first(R), last(R)
    for (i, dim) in enumerate(dims)
        I1 = CartesianIndex([i == dim ? 1 : 0 for i=1:ndims(A)]...)
        for I in R
            B[i,I] = A[min(I+I1, Ilast)] - A[max(I-I1, Ifirst)]
        end
        for I in Ifirst+I1:Ilast-I1
            B[i,I] *= 0.5
        end
    end
    return B
end


function partial(A::Array{T, N}, dims...) where {N, T}
    B = Array{T}(undef, length(dims), size(A)...)::Array{T, N + 1}
    return partial!(B, A, dims...)
end

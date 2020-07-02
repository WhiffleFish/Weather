# TODO
- [x] Wind velocity quiver plot
- [x] Add coastlines to quiver plot
- Match line contour colormap to fill contour colormap
- [x] Return fig, ax objects for post-method-call plot manipulation
- Major lat/lon lines in plot
- [x] Change longitudes from 0-360 to +-180
- [x] Format contour label to round to integer
- [x] Fix suptitle placement
- Colorbar
    - Tick Placement
        - Wind: Integers
        - Geopotential heights: Nearest 10
    - Decrease Relative Width
    - Match colorbar length to ax length
- Data Manipulation Class
    - Normalize
    - Gradient
    - date_to_day
    - day_to_date

# Pressure Distribution Classification
- Get geopot gradient and normalize
- Threshold gradients grad[grad > thresh] = 1
    - End of October continental pressure gradients dominated off-coast vortex 
- Mask gradient image to Continental East Coast
- Match Score: Sum of pixel intensities in masked image / Mask sum

## Idea 2
- dot product of all wind vectors with ideal wind vector pointing up the coast
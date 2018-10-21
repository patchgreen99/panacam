import cv2
import numpy as np
from scipy.ndimage import map_coordinates

'''
Each camera is callable so the detection of up,down,zoom movement are seperate and can be turned off 
'''

def horizontal(osrc1,osrc2, thresh=None):
    rows = np.random.randint(0, osrc1.shape[0], 50)

    src1 = cv2.cvtColor(osrc1[rows], cv2.COLOR_BGR2GRAY)
    src2 = cv2.cvtColor(osrc2[rows], cv2.COLOR_BGR2GRAY)

    src1 = np.float32(src1)
    src2 = np.float32(src2)

    # src1 = np.float32(osrc1)
    # src2 = np.float32(osrc2)

    p1 = cv2.phaseCorrelate(src1,src2)

    r = np.array(list(p1[0])).astype("int")
    return r, src2

def vertical(osrc1,osrc2, thresh=None):
    cols = np.random.randint(0, osrc1.shape[1], 50)

    src1 = cv2.cvtColor(osrc1[:,cols], cv2.COLOR_BGR2GRAY)
    src2 = cv2.cvtColor(osrc2[:,cols], cv2.COLOR_BGR2GRAY)

    src1 = np.float32(src1)
    src2 = np.float32(src2)

    # src1 = np.float32(osrc1)
    # src2 = np.float32(osrc2)

    p1 = cv2.phaseCorrelate(src1,src2)

    r = np.array(list(p1[0])).astype("int")
    return r, src2

def zoom(osrc1,osrc2, thresh=None):

    src1 = np.float32(osrc1)
    src2 = np.float32(osrc2)

    p1 = cv2.phaseCorrelate(src1,src2)

    r = np.array(list(p1[0])).astype("int")
    return r, src2

def index_coords(data, origin=None):
    """Creates x & y coords for the indicies in a numpy array "data".
    "origin" defaults to the center of the image. Specify origin=(0,0)
    to set the origin to the lower left corner of the image."""
    ny, nx = data.shape[:2]
    if origin is None:
        origin_x, origin_y = nx // 2, ny // 2
    else:
        origin_x, origin_y = origin
    x, y = np.meshgrid(np.arange(nx), np.arange(ny))
    x -= origin_x
    y -= origin_y
    return x, y

def cart2polar(x, y):
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return r, theta

def polar2cart(r, theta):
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y

def reproject_image_into_polar(data, origin):
    ny, nx = data.shape[:2]
    if origin is None:
        origin = (nx//2, ny//2)

    # Determine that the min and max r and theta coords
    x, y = index_coords(data, origin=origin)
    r, theta = cart2polar(x, y)

    # Make a regular (in polar space) grid based on the min and max r & theta
    r_i = np.linspace(r.min(), r.max(), nx)
    theta_i = np.linspace(theta.min(), theta.max(), ny)
    theta_grid, r_grid = np.meshgrid(theta_i, r_i)

    # Project the r and theta grid back into pixel coordinates
    xi, yi = polar2cart(r_grid, theta_grid)
    xi += origin[0] # We need to shift the origin back to
    yi += origin[1] # back to the lower-left corner...
    xi, yi = xi.flatten(), yi.flatten()
    coords = np.vstack((xi, yi)) # (map_coordinates requires a 2xn array)

    # Reproject each band individually and the restack
    bands = []
    for band in data.T:
        zi = map_coordinates(band, coords, order=1)
        bands.append(zi.reshape((nx, ny)))
    output = np.dstack(bands)
    return output, r_i, theta_i
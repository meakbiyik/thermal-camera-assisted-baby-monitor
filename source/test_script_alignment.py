import cv2
import numpy as np
from skimage import transform, color, restoration, feature, filters
from skimage.morphology import disk
import numba
from numba import njit
import skimage.io as io
from scipy import optimize
from matplotlib import pyplot as plt
from scipy.stats import norm, multivariate_normal
from scipy import stats

from control.transform_matrix import calculate_transform_matrix

#image adresses
frame_RGB = r'C:\Users\erena\OneDrive\Desktop\EEE 493-494\photos\ziya_baby2\rgb.jpg'
frame_thermal = r'C:\Users\erena\OneDrive\Desktop\EEE 493-494\photos\ziya_baby2\thermal.jpg'

# get images
frame_RGB = io.imread(frame_RGB)
frame_thermal = io.imread(frame_thermal)

scale_factor_of_thermal = 3

# override max height and width. 
max_height = 60*scale_factor_of_thermal
max_width = 80*scale_factor_of_thermal

# Expand-reduce frames to have the same size. Do not apply Gaussian smoothing,
# since a total-variation denoising will be done later
frame_RGB_res = transform.pyramid_reduce(frame_RGB, sigma = 0,
                                         downscale = frame_RGB.shape[0]/max_height)
frame_thermal_res = transform.pyramid_expand(frame_thermal, sigma = 0,
                                             upscale = max_height/frame_thermal.shape[0])

transform_matrix = calculate_transform_matrix(frame_RGB_res, frame_thermal_res,
                                              division_depth = 8)

trans = transform.PolynomialTransform(transform_matrix)

print(trans.params)

warped = transform.warp(frame_thermal_res,trans)

plt.figure()
plt.imshow(warped)

scaled_aligned_thermal = cv2.applyColorMap((warped*255).astype('uint8'), cv2.COLORMAP_JET)[...,::-1]

overlay = cv2.addWeighted(scaled_aligned_thermal, 0.3, (frame_RGB_res*255).astype('uint8'), 0.7, 0)
plt.figure()
plt.imshow(overlay)


## override max height and width
#scale_factor = 4
#max_height = 60*scale_factor
#max_width = 80*scale_factor
#
## Expand-reduce images to have the same size
#frame_RGB_res = transform.pyramid_reduce(frame_RGB, sigma = 0,
#                                         downscale = frame_RGB.shape[0]/max_height)
#frame_thermal_res = transform.pyramid_expand(frame_thermal, sigma = 0,
#                                             upscale = max_height/frame_thermal.shape[0])
##
##plt.figure()
##plt.imshow(frame_RGB_res)
##plt.figure()
##plt.imshow(frame_thermal_res)
#
## Get the value dimension of the RGB image, scale it to 0-255
#frame_lum = color.rgb2hsv(frame_RGB_res)[:,:,2]
#scaled_lum = ((frame_lum - np.min(frame_lum))/(np.max(frame_lum) - np.min(frame_lum))*255).astype('uint8')
#
## Smooth the images by an edge-preserving TV denoising method.
## RGB is smoothed more than thermal, since it has more unnecessary features
#lum_smooth = restoration.denoise_tv_chambolle(scaled_lum, weight=0.4, multichannel=False)
#therm_smooth = restoration.denoise_tv_chambolle(frame_thermal_res, weight=0.2, multichannel=False)
#
## Possible contours - get ideal values from minimization!
## To determine the thresholds, try to make the pixel counts on both images
## approximately equal.
#one_perc_count = max_height*max_width/100
#lum_canny_minimize = lambda th: abs(4*one_perc_count-np.count_nonzero(feature.canny(lum_smooth,
#                                                              sigma = 0,
#                                                              high_threshold = th[1],
#                                                              low_threshold  = th[0])))
#thm_canny_minimize = lambda th: abs(4*one_perc_count-np.count_nonzero(feature.canny(therm_smooth,
#                                                              sigma = 0,
#                                                              high_threshold = th[1],
#                                                              low_threshold  = th[0])))
#
#
## Get the optimizing hysteresis thresholds
#low_th_lum, high_th_lum = optimize.fmin_powell(lum_canny_minimize, np.array([0.1, 0.15]))
#low_th_thm, high_th_thm = optimize.fmin_powell(thm_canny_minimize, np.array([0.05, 0.1]))
#
## Apply canny edge detection 
#rgb_proc = feature.canny(lum_smooth, sigma = 0,
#                                 high_threshold = high_th_lum,
#                                 low_threshold = low_th_lum)
#therm_proc = feature.canny(therm_smooth, sigma = 0,
#                                   high_threshold = high_th_thm,
#                                   low_threshold = low_th_thm)
#
#plt.figure()
#plt.imshow(rgb_proc)
#plt.figure()
#plt.imshow(therm_proc)
#
## Divide image into vertical areas. Width of the regions are wider to the sides,
## since the divergence is higher. 
#points_x = []
#points_y = []
#errors = []
#weights = []
#depth = 30
#for region_count in (np.linspace(1,depth,depth)).astype(int):
#    print(region_count)
##    region_sizes = [(1-norm.pdf(i)) for i in np.linspace(-3,3,num = region_count)]
##    normalized_sizes = [size/sum(region_sizes)*max_width for size in region_sizes]
##    region_divisions = np.cumsum(normalized_sizes).astype(int)[:-1]
#    region_divisions_with_zero = np.linspace(0, max_width, num = region_count,
#                                   endpoint = False, dtype = int)
#    region_divisions = region_divisions_with_zero[1:]
#    lum_regions = np.hsplit(rgb_proc,region_divisions)
#    therm_regions = np.hsplit(therm_proc,region_divisions)
#    
#    region_divisions_with_zero = np.insert(region_divisions, 0, 0)
#    for ind, (lumreg, thermreg) in enumerate(zip(lum_regions, therm_regions)):
#        
#        shifts, error, _ = feature.register_translation(thermreg.astype(int), lumreg.astype(int), 100)
#        min_h, min_w = shifts
#
#        points_y.append(max_height/2-min_h)
#        points_x.append(region_divisions_with_zero[ind] + min_w)
#        errors.append(error)
#        weights.append(depth - region_count + 1)
#
##src = np.array([(x,y) for x,y in zip(points_x,points_y)])
##dest = np.array([(int((b+a)/2),int(max_height/2)) for a,b in zip(region_divisions_with_zero,list(region_divisions) + [max_width]) ])
#
#from sklearn.preprocessing import PolynomialFeatures
#
#clean_mask_1 = np.array([True if y > max_height*11/20 else False for y in points_y])
#semiclean_points_x = np.array(points_x)[clean_mask_1]
#semiclean_points_y = np.array(points_y)[clean_mask_1]
#semiclean_weights = np.array(weights)[clean_mask_1]
#
#q1, q3 = np.percentile(semiclean_points_y, [25 ,75])
#iqr_y = stats.iqr(semiclean_points_y)
#clean_mask_2 = np.array([True if q1 - iqr_y < y < q3 + iqr_y else False for y in semiclean_points_y])
#clean_points_x = np.array(semiclean_points_x)[clean_mask_2]
#clean_points_y = np.array(semiclean_points_y)[clean_mask_2]
#clean_weights = np.array(semiclean_weights)[clean_mask_2]
#
#poly = PolynomialFeatures(degree=2)
#X_t = poly.fit_transform(np.array(clean_points_x).reshape((-1,1)))
#
### Define the Model
### its minimum needs to be centered at the center of the image.
### therefore, max_width = -b_1 / b_2
### We only need two constants. b vector is a two-element vector.
### b_0: intercept
### b_1, b_2 = -b_1/max_width
##model = lambda b, X: (b[0] * X[:,0]) + b[1] * X[:,1] + b[2] * X[:,2]
##
### The objective Function to minimize (least-squares regression)
##obj = lambda b, Y, X: np.sum(np.abs(Y-model(b, X))**2)
##
### Initial guess for b[0], b[1]:
##xinit = np.array([1, -10, 10])
##
### Constraint: 2*b[2]*max_width + b[1] = 0
##cons = [{"type": "eq", "fun": lambda b: b[2]*max_width + b[1],
##         "jac": lambda b: [0, 1, max_width]},
##        {"type": "ineq", "fun": lambda b: b[2],
##         "jac": lambda b: [0, 0, 1]}]
##
##b_res = optimize.minimize(obj, args=(clean_points_y.reshape((-1,1)), X_t), x0=xinit,
###                         constraints=cons,
##                         options = {'disp' : True}).x
###
#from sklearn.linear_model import LinearRegression
#clf = LinearRegression()
#clf.fit(X_t, clean_points_y, sample_weight = clean_weights)
#
#points = np.linspace(0,max_width,10)
#data = poly.fit_transform(points.reshape((-1,1)))
#line = clf.predict(data)
##line = model(b_res, data)
#
#x_points_grid = np.array([points , points, points, points, points])
#y_points_grid = np.array([line-20, line-10, line, line+10, line+20])
#src = np.array([(x,y) for x,y in zip(x_points_grid.flatten(), y_points_grid.flatten())])
#cent = max_height/2
#y_points_truegrid = np.broadcast_to(np.array([[cent-20], [cent-10], [cent], [cent+10], [cent+20]]), y_points_grid.shape)
#dest = np.array([(x,y) for x,y in zip(x_points_grid.flatten(), y_points_truegrid.flatten())])
#
#trans = transform.PolynomialTransform()
#trans.estimate(src,dest,2)
#
#print(trans.params)
#
#warped = transform.warp(frame_thermal_res,trans)
#
#plt.figure()
#plt.imshow(warped)
#
#plt.figure()
#plt.imshow(frame_thermal_res)
#plt.scatter(points_x, points_y,color = 'r')
#plt.scatter(clean_points_x, clean_points_y,color = 'g')
#plt.plot(points, line)
#
#scaled_aligned_thermal = cv2.applyColorMap((warped*255).astype('uint8'), cv2.COLORMAP_JET)[...,::-1]
#
#overlay = cv2.addWeighted(scaled_aligned_thermal, 0.3, (frame_RGB_res*255).astype('uint8'), 0.7, 0)
#plt.figure()
#plt.imshow(overlay)

#
##1.826: default with njit and np.sum
##3.059: jit with np.count_nonzero
##1.842: using sum instead of or
##1.797:using "and not" instead of xor
##1.385:using "and not" instead of xor, float32
##1.373:using "and not" instead of xor, float32, declare outside of func
##1.381:using "and not" instead of xor, float32, declare outside of func, one loop instead of two
##0.404:using "and not" instead of xor, float32, declare outside of func, parallel = True
#
############
#### vertical regularizer: regularizer that is suitable for the locations
#### of the camera
############
#vert_reg = np.array([np.concatenate([np.linspace(1,0.1,int(max_width/2)),np.linspace(0.1,1,int(max_width/2))]) for i in range(max_height)])
#regularized_score = score_image*vert_reg
#
#plt.figure()
#plt.imshow(1/score_image)
#plt.figure()
#plt.imshow(1/vert_reg)
#plt.figure()
#plt.imshow(1/regularized_score, cmap = 'jet')
#
#h, w  = score_image.shape
#cent_h, cent_w = int(h/2),int(w/2)
#min_h, min_w = np.unravel_index(regularized_score.argmin(), regularized_score.shape)
#
#diff_h, diff_w = int((768/max_height)*(cent_h-min_h)), int((1024/max_width)*(cent_w-min_w))
#
##if(diff_w < 0):
##    diff_w = -diff_w
##
##diff_h = 180
#
#scaled_aligned_RGB = frame_RGB[-diff_h:,:]
#scaled_aligned_thermal = (transform.resize(frame_thermal, frame_RGB.shape,
#                                     mode = 'reflect')*255).astype(np.uint8)[:diff_h,:]
#scaled_aligned_thermal = cv2.applyColorMap(scaled_aligned_thermal, cv2.COLORMAP_JET)[...,::-1]
#
#
#overlay = (scaled_aligned_thermal*0.5 + scaled_aligned_RGB*0.5).astype(np.uint8)
#plt.figure()
#plt.imshow(overlay)

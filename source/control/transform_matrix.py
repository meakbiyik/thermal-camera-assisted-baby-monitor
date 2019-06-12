import numpy as np
from skimage import transform, color, restoration, feature
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from scipy import optimize
from scipy import stats
import cv2
from matplotlib import pyplot as plt

def float_to_uint8(frame):
    '''
    Convert float64 frame to uint8.
    
    Numba does not optimize this function, as it is pretty optimized by itself.
    Faster than the generic version of skimage.
    '''
    
    conv_frame = (frame*256).astype(np.uint8)

    return conv_frame

def _canny_with_TV(frame_RGB, weight, coverage = 3, return_error = False):
    
    if len(frame_RGB.shape) == 3:
        max_height, max_width,_ = frame_RGB.shape
    
        # Smooth the images by an edge-preserving TV denoising method.
        # Color image is smoothed more than thermal, since it has more unnecessary features
        RGB_smooth = restoration.denoise_tv_chambolle(frame_RGB, weight=weight, multichannel=True)
    
    else:
        max_height, max_width = frame_RGB.shape
    
        # Smooth the images by an edge-preserving TV denoising method.
        # Color image is smoothed more than thermal, since it has more unnecessary features
        RGB_smooth = restoration.denoise_tv_chambolle(frame_RGB, weight=weight)
      
    RGB_smooth = float_to_uint8(RGB_smooth)

    # Possible contours - get ideal values from minimization!
    # To determine the thresholds, try to make the pixel counts on both images
    # approximately equal.
    one_perc_count = max_height*max_width/100
    rgb_canny_minimize = lambda th: abs(coverage*one_perc_count-np.count_nonzero(cv2.Canny(RGB_smooth,th[0],th[1])))

    # Get the optimizing hysteresis thresholds
    thresh = optimize.fmin_powell(rgb_canny_minimize, np.array([100, 150]), disp = False)

    # Apply canny edge detection 
    rgb_proc = cv2.Canny(RGB_smooth,*thresh)
    
    rgb_proc_full = np.zeros((360, 480))
    rgb_proc_full[90:270,120:360] = rgb_proc
    
    if return_error:
        return rgb_proc_full, rgb_canny_minimize(thresh)
    else:
        return rgb_proc_full

def _calculate_transform_matrix(frame_RGB, frame_thermal,
                               thermal_canny_percentage = 4,
                               rgb_canny_percentage = 4,
                               division_depth = 6,
                               desired_thermal_scale = 1,
                               denoise_weight_rgb = 0.3, denoise_weight_thermal = 0.1,
                               degree = 2,
                               plot = False):
    '''
    Calculate the second degree polynomial transformation matrix to map the
    thermal frame on the RGB frame.

    Parameters
    ----------
    frame_RGB : ndarray
        RGB frame without alpha.
    frame_thermal : ndarray
        2D Thermal frame resized to have the same size with RGB frame.
    thermal_canny_percentage : int, optional
        Coverage of the edges for the canny output. Recommended: 2 to 6, default: 4.
    rgb_canny_percentage : int, optional
        Coverage of the edges for the canny output. Recommended: 3 to 8, default: 4.
    division_depth : int, optional
        Maximum region count for the vertical division. Needs to be chosen proportionally
        with the frames' quality and information density. Smallest division should
        not have a smaller width than the expected shift, but the outliers are mostly
        handled. Default: 8.

    Returns
    -------
    ndarray
        2x6 second degree polynomial transformation matrix.
    '''

    rgb_edge = _canny_with_TV(frame_RGB, denoise_weight_rgb, rgb_canny_percentage)
    therm_edge = _canny_with_TV(frame_thermal, denoise_weight_thermal, thermal_canny_percentage)
    
    orig_width, orig_height = rgb_edge.shape
    half_width, half_height = int(orig_width/2), int(orig_height/2)
    
    rgb_proc = np.zeros((orig_width*2, orig_height*2))
    rgb_proc[half_width:half_width*3,half_height:half_height*3] = rgb_edge
    therm_proc = np.zeros((orig_width*2, orig_height*2))
    therm_proc[half_width:half_width*3,half_height:half_height*3] = therm_edge
    max_width, max_height = rgb_proc.shape[:2]
    
    # Divide image into vertical areas and save the centers before a possible shift.
    points_x = []
    points_y = []
    weights = []
    for region_count in (np.logspace(0,division_depth,division_depth, base = 2)).astype(int):

        # Determine division limits
        region_divisions_with_zero = np.linspace(0, max_width, num = region_count,
                                                 endpoint = False, dtype = int)
        region_divisions = region_divisions_with_zero[1:]
        all_region_bounds = np.append(region_divisions_with_zero, max_width)
        # Divide the frames into the regions
        lum_regions = np.hsplit(rgb_proc,region_divisions)
        therm_regions = np.hsplit(therm_proc,region_divisions)
        
        region_divisions_with_zero = np.insert(region_divisions, 0, 0)
        # Calculate the shifts for each region and save the points. Weight of a point
        # is proportional with its size ( thus, amount of information) and its
        # closeness to the center of the image ( which is the expected location
        # of the baby)
        for ind, (lumreg, thermreg) in enumerate(zip(lum_regions, therm_regions)):
            
            shifts, error, _ = feature.register_translation(thermreg.astype(int), lumreg.astype(int), 10)
            min_h, min_w = shifts
    
            reg_width = all_region_bounds[ind+1] - region_divisions_with_zero[ind]
            point_y = max_height/2-min_h
            point_x = region_divisions_with_zero[ind] + reg_width/2 - min_w
            
            points_y.append(point_y)
            points_x.append(point_x)

            sum_t = np.count_nonzero(thermreg)
            sum_r = np.count_nonzero(lumreg)
            try:
                weights.append(sum_t*sum_r/(sum_t+sum_r))
            except ZeroDivisionError:
                weights.append(0)
#           weights.append(reg_width*max_height)
#            weights.append( (division_depth - region_count + 1) * abs(point_x-(max_width/2))/max_width )
    
    # Remove the points that are certainly miscalculations: First filter by
    # the location of the cameras, then remove outliers (i.e. points more than 1 iqr away 
    # from the closest percentile.)
    
    clean_mask_1 = np.array([True if y > max_height*11/20 else False for y in points_y])
    clean_mask_1 = np.array([True if True else False for y in points_y])
    semiclean_points_x = np.array(points_x)[clean_mask_1]
    semiclean_points_y = np.array(points_y)[clean_mask_1]
    semiclean_weights = np.array(weights)[clean_mask_1]
    
    from collections import Counter
    #weighted percentiles
    q1, q3 = np.percentile(list(Counter(dict(zip(semiclean_points_y, semiclean_weights.astype(int)))).elements()), [25 ,75])
    #q1, q3 = np.percentile(semiclean_points_y, [25 ,75])
    iqr_y = (q3-q1)*1
    clean_mask_2 = np.array([True if q1 - iqr_y < y < q3 + iqr_y else False for y in semiclean_points_y])
    clean_points_x = np.array(semiclean_points_x)[clean_mask_2]
    clean_points_y = np.array(semiclean_points_y)[clean_mask_2]
    clean_weights = np.array(semiclean_weights)[clean_mask_2]

    # Create the polynomial features and fit the regression.
    poly = PolynomialFeatures(degree=degree)
    X_t = poly.fit_transform(np.array(clean_points_x).reshape((-1,1)))
    
    clf = LinearRegression()
    clf.fit(X_t, clean_points_y, sample_weight = clean_weights)
    
    points = np.linspace(0,max_width,10)
    data = poly.fit_transform(points.reshape((-1,1)))
    line = clf.predict(data)
    
    # Create a grid of values from the regression to estimate the transformation matrix.
    x_points_grid = np.array([points , points, points, points, points])
    y_points_grid = np.array([line-20, line-10, line, line+10, line+20])
    src = np.array([(x-half_width,y-half_height) for x,y in zip(x_points_grid.flatten(), y_points_grid.flatten())])
    cent = max_height/2
    y_points_truegrid = np.broadcast_to(np.array([[cent-20], [cent-10], [cent], [cent+10], [cent+20]]), y_points_grid.shape)
    dest = np.array([(x-half_width,y-half_height) for x,y in zip(x_points_grid.flatten(), y_points_truegrid.flatten())])
    
    trans = transform.PolynomialTransform()
    trans.estimate(src*desired_thermal_scale,dest*desired_thermal_scale,degree)
    
    if plot:
        
        import cv2
        fig, ax = plt.subplots(nrows=1, ncols=5, figsize = (20,5))
        
        ax[0].imshow(frame_thermal)
        ax[0].set_title('thermal frame. Initial res: 80x60')
        ax[1].imshow(frame_RGB)
        ax[1].set_title('RGB frame. Initial res: 640x480')
        ax[2].imshow(frame_thermal)
        ax[2].scatter(points_x, points_y,color = 'r')
        ax[2].scatter(clean_points_x, clean_points_y,color = 'g')
        ax[2].plot(points, line,scalex = False, scaley= False)
        ax[2].set_xlim(0,max_height)
        ax[2].set_ylim(max_width,0)
        ax[2].set_title('Corr. points and the quadratic fit. Red: outliers.')
        ax[3].imshow(therm_proc)
        ax[3].set_title('Edges of thermal frame')
        
        warped = transform.warp(frame_thermal,trans)
        
        scaled_aligned_thermal = cv2.applyColorMap((warped*256).astype('uint8'), cv2.COLORMAP_JET)[...,::-1]
        
        overlay = cv2.addWeighted(scaled_aligned_thermal, 0.3, (frame_RGB).astype('uint8'), 0.7, 0)
        ax[4].imshow(overlay)
        ax[4].set_title('final overlay')
    
    return trans.params

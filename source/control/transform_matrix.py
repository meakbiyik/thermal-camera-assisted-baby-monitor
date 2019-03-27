import numpy as np
from skimage import transform, color, restoration, feature
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from scipy import optimize
from scipy import stats

def calculate_transform_matrix(frame_RGB, frame_thermal,
                               thermal_canny_percentage = 4,
                               rgb_canny_percentage = 4,
                               division_depth = 8):
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
    
    # Frames must be equal in size.
    assert frame_RGB.shape[:2] == frame_thermal.shape, "Frames have different size!"
    
    max_height, max_width = frame_thermal.shape
    
    # Get the value dimension of the RGB image
    frame_val = color.rgb2hsv(frame_RGB)[:,:,2]

    # Smooth the images by an edge-preserving TV denoising method.
    # Color image is smoothed more than thermal, since it has more unnecessary features
    val_smooth = restoration.denoise_tv_chambolle(frame_val, weight=0.4, multichannel=False)
    therm_smooth = restoration.denoise_tv_chambolle(frame_thermal, weight=0.2, multichannel=False)
    
    # Possible contours - get ideal values from minimization!
    # To determine the thresholds, try to make the pixel counts on both images
    # approximately equal.
    one_perc_count = max_height*max_width/100
    val_canny_minimize = lambda th: abs(rgb_canny_percentage*one_perc_count-np.count_nonzero(feature.canny(val_smooth,
                                                                  sigma = 0,
                                                                  high_threshold = th[1],
                                                                  low_threshold  = th[0])))
    thm_canny_minimize = lambda th: abs(thermal_canny_percentage*one_perc_count-np.count_nonzero(feature.canny(therm_smooth,
                                                                  sigma = 0,
                                                                  high_threshold = th[1],
                                                                  low_threshold  = th[0])))
    # Get the optimizing hysteresis thresholds
    low_th_val, high_th_val = optimize.fmin_powell(val_canny_minimize, np.array([0.1, 0.15]))
    low_th_thm, high_th_thm = optimize.fmin_powell(thm_canny_minimize, np.array([0.05, 0.1]))
    
    # Apply canny edge detection 
    rgb_proc = feature.canny(val_smooth, sigma = 0,
                             high_threshold = high_th_val,
                             low_threshold = low_th_val)
    therm_proc = feature.canny(therm_smooth, sigma = 0,
                               high_threshold = high_th_thm,
                               low_threshold = low_th_thm)
    
    
    # Divide image into vertical areas and save the centers before a possible shift.
    points_x = []
    points_y = []
    weights = []
    for region_count in (np.linspace(1,division_depth,division_depth)).astype(int):

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
            
            shifts, error, _ = feature.register_translation(thermreg.astype(int), lumreg.astype(int), 100)
            min_h, min_w = shifts
    
            reg_width = all_region_bounds[ind+1] - region_divisions_with_zero[ind]
            point_y = max_height/2-min_h
            point_x = region_divisions_with_zero[ind] + reg_width/2 - min_w
            
            points_y.append(point_y)
            points_x.append(point_x)

            weights.append( (division_depth - region_count + 1) * abs(point_x-(max_width/2))/max_width )
    
    # Remove the points that are certainly miscalculations: First filter by
    # the location of the cameras, then remove outliers (i.e. points more than 1 iqr away 
    # from the closest percentile.)
    clean_mask_1 = np.array([True if y > max_height*11/20 else False for y in points_y])
    semiclean_points_x = np.array(points_x)[clean_mask_1]
    semiclean_points_y = np.array(points_y)[clean_mask_1]
    semiclean_weights = np.array(weights)[clean_mask_1]
    
    q1, q3 = np.percentile(semiclean_points_y, [25 ,75])
    iqr_y = stats.iqr(semiclean_points_y)
    clean_mask_2 = np.array([True if q1 - iqr_y < y < q3 + iqr_y else False for y in semiclean_points_y])
    clean_points_x = np.array(semiclean_points_x)[clean_mask_2]
    clean_points_y = np.array(semiclean_points_y)[clean_mask_2]
    clean_weights = np.array(semiclean_weights)[clean_mask_2]
    
    # Create the polynomial features and fit the regression.
    poly = PolynomialFeatures(degree=2)
    X_t = poly.fit_transform(np.array(clean_points_x).reshape((-1,1)))
    
    clf = LinearRegression()
    clf.fit(X_t, clean_points_y, sample_weight = clean_weights)
    
    points = np.linspace(0,max_width,10)
    data = poly.fit_transform(points.reshape((-1,1)))
    line = clf.predict(data)
    
    # Create a grid of values from the regression to estimate the transformation matrix.
    x_points_grid = np.array([points , points, points, points, points])
    y_points_grid = np.array([line-20, line-10, line, line+10, line+20])
    src = np.array([(x,y) for x,y in zip(x_points_grid.flatten(), y_points_grid.flatten())])
    cent = max_height/2
    y_points_truegrid = np.broadcast_to(np.array([[cent-20], [cent-10], [cent], [cent+10], [cent+20]]), y_points_grid.shape)
    dest = np.array([(x,y) for x,y in zip(x_points_grid.flatten(), y_points_truegrid.flatten())])
    
    trans = transform.PolynomialTransform()
    trans.estimate(src/3,dest/3,2)
    
    from matplotlib import pyplot as plt
    import cv2
    fig, ax = plt.subplots(nrows=1, ncols=4, figsize = (20,5))
    
    ax[0].imshow(frame_thermal)
    ax[0].set_title('thermal frame. Initial res: 80x60')
    ax[1].imshow(frame_RGB)
    ax[1].set_title('RGB frame. Initial res: 640x480')
    ax[2].imshow(frame_thermal)
    ax[2].scatter(points_x, points_y,color = 'r')
    ax[2].scatter(clean_points_x, clean_points_y,color = 'g')
    ax[2].plot(points, line)
    ax[2].set_title('Corr. points and the quadratic fit. Red: outliers.')
    
    warped = transform.warp(frame_thermal,trans)
    
    scaled_aligned_thermal = cv2.applyColorMap((warped*256).astype('uint8'), cv2.COLORMAP_JET)[...,::-1]
    
    overlay = cv2.addWeighted(scaled_aligned_thermal, 0.3, (frame_RGB).astype('uint8'), 0.7, 0)
    ax[3].imshow(overlay)
    ax[3].set_title('final overlay')
    
    return trans.params

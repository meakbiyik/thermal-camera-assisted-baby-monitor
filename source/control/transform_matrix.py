import numpy as np
from skimage import transform, color, restoration, feature
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from scipy import optimize
from scipy import stats

def calculate_transform_matrix(frame_RGB, frame_thermal,
                                thermal_canny_percentage = 4,
                                RGB_canny_percentage = 4,
                                division_depth = 8):
    
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
    val_canny_minimize = lambda th: abs(RGB_canny_percentage*one_perc_count-np.count_nonzero(feature.canny(val_smooth,
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
    
    
    # Divide image into vertical areas. Width of the regions are wider to the sides,
    # since the divergence is higher. 
    points_x = []
    points_y = []
    weights = []
    for region_count in (np.linspace(1,division_depth,division_depth)).astype(int):

        region_divisions_with_zero = np.linspace(0, max_width, num = region_count,
                                       endpoint = False, dtype = int)
        region_divisions = region_divisions_with_zero[1:]
        lum_regions = np.hsplit(rgb_proc,region_divisions)
        therm_regions = np.hsplit(therm_proc,region_divisions)
        
        region_divisions_with_zero = np.insert(region_divisions, 0, 0)
        for ind, (lumreg, thermreg) in enumerate(zip(lum_regions, therm_regions)):
            
            shifts, error, _ = feature.register_translation(thermreg.astype(int), lumreg.astype(int), 100)
            min_h, min_w = shifts
    
            points_y.append(max_height/2-min_h)
            points_x.append(region_divisions_with_zero[ind] + min_w)
            weights.append(division_depth - region_count + 1)
    
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
    
    poly = PolynomialFeatures(degree=2)
    X_t = poly.fit_transform(np.array(clean_points_x).reshape((-1,1)))
    
    clf = LinearRegression()
    clf.fit(X_t, clean_points_y, sample_weight = clean_weights)
    
    points = np.linspace(0,max_width,10)
    data = poly.fit_transform(points.reshape((-1,1)))
    line = clf.predict(data)
    
    x_points_grid = np.array([points , points, points, points, points])
    y_points_grid = np.array([line-20, line-10, line, line+10, line+20])
    src = np.array([(x,y) for x,y in zip(x_points_grid.flatten(), y_points_grid.flatten())])
    cent = max_height/2
    y_points_truegrid = np.broadcast_to(np.array([[cent-20], [cent-10], [cent], [cent+10], [cent+20]]), y_points_grid.shape)
    dest = np.array([(x,y) for x,y in zip(x_points_grid.flatten(), y_points_truegrid.flatten())])
    
    trans = transform.PolynomialTransform()
    trans.estimate(src,dest,2)
    
    from matplotlib import pyplot as plt
    plt.figure()
    plt.imshow(frame_thermal)
    plt.scatter(points_x, points_y,color = 'r')
    plt.scatter(clean_points_x, clean_points_y,color = 'g')
    plt.plot(points, line)
    
    return trans.params
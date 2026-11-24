# create_fake_homography.py
import numpy as np
# This makes an identity homography; allows main.py --simulate to run without real calibration.
H = np.eye(3, dtype='float32')
np.save("homography.npy", H)
print("Saved fake homography.npy (identity). Only for home testing.")

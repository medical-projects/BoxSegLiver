# Copyright 2019 Jianwei Zhang All Right Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# =================================================================================

import json
import numpy as np
from pathlib import Path
from matplotlib import rcParams, font_manager
rcParams['font.family'] = 'Times New Roman'
del font_manager.weight_dict['roman']
font_manager._rebuild()

import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from DataLoader.Liver import nii_kits
from skimage import feature


def curve(root):
    json_file = root / "prepare/meta.json"
    with json_file.open() as f:
        meta = json.load(f)
    meta = {x["PID"]: x for x in meta}

    size = []
    spacing = []
    tumors = []
    for i, x in meta.items():
        size.append(x["size"])
        spacing.append(x["spacing"])
        tumors.extend(x["tumors"])
    size = np.array(size)
    spacing = np.array(spacing)
    print(size.max(0), size.min(0), size.mean(0))
    print(spacing.max(0), spacing.min(0))
    print(len(tumors))

    # print()
    # all_rates = []
    # for i, x, in meta.items():
    #     for j, y in enumerate(x["tumor_slices"]):
    #         rate = (y[2] - y[0]) / (y[3] - y[1])
    #         all_rates.append(rate)
    #         if rate > 8 or rate < 0.125:
    #             cnt = 0
    #             for k in x["tumor_slices_from_to"][1:]:
    #                 if j < k:
    #                     break
    #                 cnt += 1
    #             print(i, x["tumor_slices_index"][cnt], round(rate, 3), y)
    # plt.hist(all_rates, bins=50)
    # plt.show()

    indices = []
    tumor_volume = []
    for i, x in meta.items():
        voxel_volume = x["spacing"][0] * x["spacing"][1] * x["spacing"][2]
        for t in x["tumor_areas"]:
            tumor_volume.append(t * voxel_volume)
            indices.append(i)
    tumor_volume = np.array(tumor_volume) / 1000

    print(tumor_volume.max(), tumor_volume.min(), indices[tumor_volume.argmax()])
    return tumor_volume


fs = 40
# ----------------------------------------------------------------------------------------------
# Plot tumor size
#
fig, ax = plt.subplots(1, 1, figsize=(12, 12))
tumor_volume = curve(Path(__file__).parent)
density = gaussian_kde(tumor_volume)
density.covariance_factor = lambda: .25
density._compute_covariance()
xs = np.logspace(0, 4, 100)
ax.plot(xs, density(xs), linewidth=5)

# tumor_volume = curve(Path(__file__).parent.parent / "Liver")
# density = gaussian_kde(tumor_volume)
# density.covariance_factor = lambda: .25
# density._compute_covariance()
# xs = np.logspace(0, 3, 100)
# ax.plot(xs, density(xs), linewidth=5)

ax.set_xscale('log')
ax.tick_params(axis='both', which='major', labelsize=fs)
ax.set_xlabel('Tumor volume in log scale (cm$^3$)', fontsize=fs)
ax.set_ylabel('Probability', fontsize=fs)
ax.legend(["Neurofibroma"], fontsize=fs)

plt.tight_layout()
plt.show()

# ----------------------------------------------------------------------------------------------

# _, volume = nii_kits.read_lits(1, "vol", "E:/DataSet/LiTS/Training_Batch/volume-1.nii")
# _, labels = nii_kits.read_lits(1, "lab", "E:/DataSet/LiTS/Training_Batch/segmentation-1.nii")
# liver = volume[labels > 0]
# tumor = volume[labels == 2]
#
# fig, ax = plt.subplots(1, 2)
# ax[0].hist(liver, bins=100, range=(0, 200), density=True)
# ax[0].hist(tumor, bins=100, range=(0, 200), density=True)
# ax[0].set_xlabel('Hounsfield unit', fontsize=15)
# ax[0].set_ylabel('Normalized frequency', fontsize=15)
# ax[0].tick_params(axis='both', which='major', labelsize=15)
# ax[0].legend(["Liver", "Tumor"], fontsize=15)
# ax[0].set_title("volume-1.nii", fontsize=15)
#
# _, volume = nii_kits.read_lits(45, "vol", "E:/DataSet/LiTS/Training_Batch/volume-45.nii")
# _, labels = nii_kits.read_lits(45, "lab", "E:/DataSet/LiTS/Training_Batch/segmentation-45.nii")
# liver = volume[labels > 0]
# tumor = volume[labels == 2]
#
# ax[1].hist(liver, bins=100, range=(0, 200), density=True)
# ax[1].hist(tumor, bins=100, range=(0, 200), density=True)
# ax[1].set_xlabel('Hounsfield unit', fontsize=15)
# ax[1].tick_params(axis='both', which='major', labelsize=15)
# ax[1].tick_params(axis='y', which='both', labelsize=15, left=False, labelleft=False)
# ax[1].legend(["Liver", "Tumor"], fontsize=15)
# ax[1].set_title("volume-45.nii", fontsize=15)
#


def show(x):
    ah, a = nii_kits.read_nii("E:/Dataset/Neurofibromatosis/nii_NF/volume-{:03d}.nii.gz".format(x))
    bh, b = nii_kits.read_nii("E:/Dataset/Neurofibromatosis/nii_NF/segmentation-{:03d}.nii.gz".format(x))
    b = np.clip(b, 0, 1)
    a2 = a * b
    plt.hist(a2[a2 > 0], bins=150, range=(0, 900), density=True)
    plt.show()


#--------------------------------------------------------------------------------------------------------------------
# Plot glcm
#
# fig, ax = plt.subplots(2, 3, figsize=(16, 10))
# GRAY_MIN, GRAY_MAX = -200, 250
# json_file = Path(__file__).parent.parent / "Liver/prepare/meta.json"
# with json_file.open() as f:
#     meta = json.load(f)
# meta = {x["PID"]: x for x in meta}
#
# for j, (jj, stids) in enumerate(zip([2, 45], [[9, 12, 15], [4, 7, 10]])):
#     _, volume = nii_kits.read_lits(jj, "vol", "E:/DataSet/LiTS/Training_Batch/volume-{}.nii".format(jj))
#     volume = (np.clip(volume, GRAY_MIN, GRAY_MAX) - GRAY_MIN) * (255. / (GRAY_MAX - GRAY_MIN))
#     volume = volume.astype(np.uint8)
#
#     for k, stid in enumerate(stids):
#         y1, x1, y2, x2 = meta[jj]["tumor_slices"][stid]
#         print(y1, x1, y2, x2)
#         ii = 0
#         for i in range(1, len(meta[jj]["tumor_slices_from_to"])):
#             if i > stid:
#                 break
#             ii += 1
#         image_patch = volume[meta[jj]["tumor_slices_index"][ii], y1:y2, x1:x2]
#         print(image_patch.max(), image_patch.min())
#         glcm = feature.greycomatrix(image_patch, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
#
#         ax[j, k].imshow(glcm[:, :, 0, 0], cmap="gray")
#         ax[j, k].tick_params(axis='both', which='both', left=False, bottom=False, labelbottom=False, labelleft=False)
#         if k == 0:
#             if j == 0:
#                 ax[j, k].set_ylabel('volume 2', fontsize=30)
#             if j == 1:
#                 ax[j, k].set_ylabel('volume 45', fontsize=30)
#
# plt.tight_layout()
# plt.show()

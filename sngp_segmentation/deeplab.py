from pathlib import Path

import torch.nn as nn
from torch.nn.utils import spectral_norm
from torchvision.models.segmentation import deeplabv3_resnet101, deeplabv3_resnet50

from .utils import convleaves, getattrrecur, setattrrecur
from .unet import RandomFeatureGaussianProcess, Cos

def construct_deeplabv3_resnet50(weights: Path | None):
    if weights:
        assert weights.exists()

    model = deeplabv3_resnet50(
        weights=weights
        # i think everything else should be okay as defaults, we're directly
        # comparing against a pascal-VOC baseline.
    )

    return model


class SNGPDeepLabV3_Resnet50(nn.Module):
    def __init__(self, n_channels, n_classes, bilinear=False, weights: Path | None = None):
        super().__init__()
        module = construct_deeplabv3_resnet50(weights)
        
        for name, _ in convleaves(module):
            setattrrecur(module, name, spectral_norm(getattrrecur(module, name)))

        self.module = module

        self.rfgp = RandomFeatureGaussianProcess(
            in_features=64,
            out_features=n_classes,
            backbone=self.module,
            n_inducing=1024,
            momentum = 0.99,
            ridge_penalty = 1e-6,
            activation = Cos(), # torch.nn.Sigmoid(),
            verbose = False,
        )
        
    def forward(self, x, with_variance: bool = False, update_precision: bool = True):

        return self.rfgp(x, with_variance, update_precision)




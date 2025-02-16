# os.environ["CUDA_VISIBLE_DEVICES"] = "0"    # choose GPU if you are on a multi GPU server
import os

import PIL
import torch
import pytorch_lightning as pl
import torch.nn as nn
import clip
from PIL import Image, ImageFile


# if you changed the MLP architecture during training, change it also here:
class MLP(pl.LightningModule):
    def __init__(self, input_size, xcol='emb', ycol='avg_rating'):
        super().__init__()
        self.input_size = input_size
        self.xcol = xcol
        self.ycol = ycol
        self.layers = nn.Sequential(
            nn.Linear(self.input_size, 1024),
            # nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(1024, 128),
            # nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            # nn.ReLU(),
            nn.Dropout(0.1),

            nn.Linear(64, 16),
            # nn.ReLU(),

            nn.Linear(16, 1)
        )

    def forward(self, x):
        return self.layers(x)

    def training_step(self, batch, batch_idx):
        x = batch[self.xcol]
        y = batch[self.ycol].reshape(-1, 1)
        x_hat = self.layers(x)
        loss = F.mse_loss(x_hat, y)
        return loss

    def validation_step(self, batch, batch_idx):
        x = batch[self.xcol]
        y = batch[self.ycol].reshape(-1, 1)
        x_hat = self.layers(x)
        loss = F.mse_loss(x_hat, y)
        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer


def normalized(a, axis=-1, order=2):
    import numpy as np  # pylint: disable=import-outside-toplevel

    l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
    l2[l2 == 0] = 1
    return a / np.expand_dims(l2, axis)


model = MLP(768)  # CLIP embedding dim is 768 for CLIP ViT L 14
device = "cuda" if torch.cuda.is_available() else "cpu"
#device = "cpu"
print('device = {}'.format(device))

dir = os.path.dirname(os.path.realpath(__file__))
s = torch.load(os.path.join(dir, '..', "sac+logos+ava1-l14-linearMSE.pth"), map_location=torch.device(
    device))  # load the model you trained previously or the model available in this repo

model.load_state_dict(s)

model.to(device)
model.eval()

model2, preprocess = clip.load("ViT-L/14", device=device)  # RN50x64


def get_aesthetic_score(img_path):
    try:
        pil_image = Image.open(img_path)
    except PIL.UnidentifiedImageError:
        return None

    image = preprocess(pil_image).unsqueeze(0).to(device)

    with torch.no_grad():
        image_features = model2.encode_image(image)

    im_emb_arr = normalized(image_features.cpu().detach().numpy())

    prediction = None

    if device == 'cpu':
        prediction = model(torch.from_numpy(im_emb_arr).to(device).type(torch.FloatTensor))
    else:
        prediction = model(torch.from_numpy(im_emb_arr).to(device).type(torch.cuda.FloatTensor))

    return prediction.item()


if __name__ == "__main__":
    file_name = '../images/test.png'
    score = get_aesthetic_score(file_name)
    print(score)

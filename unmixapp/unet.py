import torch
from torch import nn


class ConvModel(nn.Module):
    def __init__(self, input_channel, output_channel):
        super().__init__()
        self.conv1 = nn.Conv2d(input_channel, output_channel, 3)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv2d(output_channel, output_channel, 3)

    def forward(self, x):
        return self.relu(self.conv2(self.relu(self.conv1(x))))


class Concatenate(nn.Module):
    def __init__(self):
        super(Concatenate, self).__init__()

    def forward(self, layer_1, layer_2):
        x = torch.cat((layer_1, layer_2), 1)

        return x


class Encoder(nn.Module):
    def __init__(self,
                 in_channels: int,
                 out_channels: int,
                 pooling: bool = True,
                 activation: str = 'relu',):
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.pooling = pooling
        self.padding = 1
        self.activation = activation

        self.conv1 = nn.Conv2d(self.in_channels, self.out_channels, kernel_size=3, stride=1,
                               padding=self.padding)

        self.conv2 = nn.Conv2d(self.out_channels, self.out_channels, kernel_size=3, stride=1,
                               padding=self.padding, )

        if self.pooling:
            self.pool = nn.MaxPool2d(kernel_size=2, stride=2, padding=0)

        if self.activation == 'relu':
            self.act1 = nn.ReLU()
            self.act2 = nn.ReLU()
        elif activation == 'leaky':
            self.act1 = nn.LeakyReLU()
            self.act2 = nn.LeakyReLU()

    def forward(self, x):
        y = self.conv1(x)
        y = self.act1(y)

        y = self.conv2(y)
        y = self.act2(y)

        before_pooling = y
        if self.pooling:
            y = self.pool(y)
        return y, before_pooling


class Decoder(nn.Module):
    def __init__(self,
                 in_channels: int,
                 out_channels: int,
                 activation: str = 'relu',

                 ):
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.padding = 1

        self.activation = activation
        self.up = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)

        self.conv1 = nn.Conv2d(2 * self.out_channels, self.out_channels, kernel_size=3, stride=1, padding=self.padding)
        self.conv2 = nn.Conv2d(self.out_channels, self.out_channels, kernel_size=3, stride=1, padding=self.padding)

        if self.activation == 'relu':
            self.act0 = nn.ReLU()
            self.act1 = nn.ReLU()
            self.act2 = nn.ReLU()
        elif activation == 'leaky':
            self.act0 = nn.LeakyReLU()
            self.act1 = nn.LeakyReLU()
            self.act2 = nn.LeakyReLU()

        self.concat = Concatenate()

    def forward(self, encoder_layer, decoder_layer):
        """ Forward pass
        Arguments:
            encoder_layer: Tensor from the encoder pathway
            decoder_layer: Tensor from the decoder pathway (to be up'd)
        """
        up_layer = self.up(decoder_layer)  # up-convolution/up-sampling
        # cropped_encoder_layer, dec_layer = autocrop(encoder_layer, up_layer)  # cropping

        # if self.up_mode != 'transposed':
        #     # We need to reduce the channel dimension with a conv layer
        #     up_layer = self.conv0(up_layer)  # convolution 0
        up_layer = self.act0(up_layer)  # activation 0
        # if self.normalization:
        #     up_layer = self.norm0(up_layer)  # normalization 0

        merged_layer = self.concat(up_layer, encoder_layer)  # concatenation
        y = self.conv1(merged_layer)  # convolution 1
        y = self.act1(y)  # activation 1
        # if self.normalization:
        #     y = self.norm1(y)  # normalization 1
        y = self.conv2(y)  # convolution 2
        y = self.act2(y)  # acivation 2
        # if self.normalization:
        #     y = self.norm2(y)  # normalization 2
        return y


class UNet(nn.Module):
    def __init__(self,
                 in_channels: int = 1,
                 out_channels: int = 2,
                 n_blocks: int = 4,
                 start_filters: int = 32,
                 ):
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.n_blocks = n_blocks
        self.start_filters = start_filters

        self.down_blocks = []
        self.up_blocks = []

        num_filters_out = 0
        for i in range(self.n_blocks):
            num_filters_in = self.in_channels if i == 0 else num_filters_out
            num_filters_out = self.start_filters * (2 ** i)
            pooling = True if i < self.n_blocks - 1 else False

            down_block = Encoder(in_channels=num_filters_in,
                                 out_channels=num_filters_out,
                                 pooling=pooling,)

            self.down_blocks.append(down_block)

        # create decoder path (requires only n_blocks-1 blocks)
        for i in range(n_blocks - 1):
            num_filters_in = num_filters_out
            num_filters_out = num_filters_in // 2

            up_block = Decoder(in_channels=num_filters_in,
                               out_channels=num_filters_out,
                               )

            self.up_blocks.append(up_block)

        self.conv_final = nn.Conv2d(num_filters_out, self.out_channels, kernel_size=1, stride=1, padding=0)

        self.down_blocks = nn.ModuleList(self.down_blocks)
        self.up_blocks = nn.ModuleList(self.up_blocks)

        self.initialize_parameters()

    @staticmethod
    def weight_init(module, method, **kwargs):
        if isinstance(module, (nn.Conv3d, nn.Conv2d, nn.ConvTranspose3d, nn.ConvTranspose2d)):
            method(module.weight, **kwargs)  # weights

    @staticmethod
    def bias_init(module, method, **kwargs):
        if isinstance(module, (nn.Conv3d, nn.Conv2d, nn.ConvTranspose3d, nn.ConvTranspose2d)):
            method(module.bias, **kwargs)  # bias

    def initialize_parameters(self,
                              method_weights=nn.init.xavier_uniform_,
                              method_bias=nn.init.zeros_,
                              kwargs_weights={},
                              kwargs_bias={}
                              ):
        for module in self.modules():
            self.weight_init(module, method_weights, **kwargs_weights)  # initialize weights
            self.bias_init(module, method_bias, **kwargs_bias)  # initialize bias

    def forward(self, x: torch.tensor):
        encoder_output = []

        # Encoder pathway
        for module in self.down_blocks:
            x, before_pooling = module(x)
            encoder_output.append(before_pooling)

        # Decoder pathway
        for i, module in enumerate(self.up_blocks):
            before_pool = encoder_output[-(i + 2)]
            x = module(before_pool, x)

        x = self.conv_final(x)
        # x = torch.relu(torch.sign(torch.sigmoid(x) - 0.5))

        return x

    def __repr__(self):
        attributes = {attr_key: self.__dict__[attr_key] for attr_key in self.__dict__.keys() if
                      '_' not in attr_key[0] and 'training' not in attr_key}
        d = {self.__class__.__name__: attributes}
        return f'{d}'

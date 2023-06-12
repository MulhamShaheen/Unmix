from .controllers import UnetController, AudioProcessor

UVocalController = UnetController(
    input_length=48,
    sample_rate=44100,
    in_channels=1,
    out_channels=1,
    n_blocks=4,
    start_filters=16,
    trained_model="unmixapp/weights/vocal.pt",
)

UBassController = UnetController(
    input_length=48,
    sample_rate=44100,
    in_channels=1,
    out_channels=1,
    n_blocks=4,
    start_filters=16,
    trained_model="unmixapp/weights/bass.pt",
)

UDrumsController = UnetController(
    input_length=48,
    sample_rate=44100,
    in_channels=1,
    out_channels=1,
    n_blocks=4,
    start_filters=16,
    trained_model="unmixapp/weights/drums.pt",
)

URestController = UnetController(
    input_length=48,
    sample_rate=44100,
    in_channels=1,
    out_channels=1,
    n_blocks=4,
    start_filters=16,
    trained_model="unmixapp/weights/rest.pt",
)

window_size = 2047
hop_length = 517
sample_rate = 44100

audioController = AudioProcessor(
    n_fft=2047,
    hop_length=517,
    sample_rate=44100
)

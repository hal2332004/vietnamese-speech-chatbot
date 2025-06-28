import torch

print("Checking CUDA availability...")
if torch.cuda.is_available():
    print("CUDA is available!")
    print(f"Number of CUDA devices: {torch.cuda.device_count()}")
    print(f"Current CUDA device index: {torch.cuda.current_device()}")
    print(f"Current CUDA device name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
else:
    print("CUDA is not available. Using CPU.")

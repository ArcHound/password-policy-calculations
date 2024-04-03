card_mapping = {
    "A100": ["A100-PCIE-40GB", "A100-SXM4-40GB"],
    "H100": ["NVIDIA H100 PCIe"],
    "V100": ["Tesla V100-SXM2-16GB"],
    "P100": ["Tesla P100-PCIE-16GB"],
    "T4": ["Tesla T4"],
    "A5000": ["NVIDIA RTX A5000"],
    "GTX 1080 Ti": ["GeForce GTX 1080 Ti", "NVIDIA GeForce GTX 1080 Ti"],
    "RTX 2070": ["GeForce RTX 2070 SUPER", "NVIDIA GeForce RTX 2070 SUPER"],
    "RTX 2080 Ti": ["GeForce RTX 2080 Ti", "NVIDIA GeForce RTX 2080 Ti"],
    "RTX 3080": ["GeForce RTX 3080", "NVIDIA GeForce RTX 3080"],
    "RTX 3080 Ti": ["GeForce RTX 3080 Ti", "NVIDIA GeForce RTX 3080 Ti"],
    "RTX 3090": ["GeForce RTX 3090", "NVIDIA GeForce RTX 3090"],
    "RTX 3090 Ti": ["GeForce RTX 3090 Ti", "NVIDIA GeForce RTX 3090 Ti"],
    "RTX 4090": ["GeForce RTX 4090", "NVIDIA GeForce RTX 4090"],
    "RTX 4090 Ti": ["GeForce RTX 4090 Ti", "NVIDIA GeForce RTX 4090 Ti"],
}

cards_list = list(card_mapping.keys())


def normalize_device(device):
    if "#" in device:
        new_dev = device.split(" #")[0]
    else:
        new_dev = device
    for c in card_mapping:
        if new_dev in card_mapping[c]:
            return c


charset_lenghts = {
    "numbers": 10,
    "lowercase": 26,
    "lowercase+uppercase": 52,
    "lowercase+uppercase+number": 62,
    "ascii_printable": 95,
}


def calculate_policy_size(charset_len, password_len):
    return pow(float(charset_len), password_len)

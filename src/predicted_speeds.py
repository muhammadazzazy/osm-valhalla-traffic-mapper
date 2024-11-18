# import the necessary packages
import numpy as np
import struct
import base64

kCoefficientCount = 10
kBucketsPerWeek = 168
kSpeedNormalization = 0.031497039
k1OverSqrt2 = 1.0 / np.sqrt(2)
kDecodedSpeedSize = kCoefficientCount * 2  # Each coefficient is 2 bytes

class BucketCosTable:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BucketCosTable, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.table = np.zeros((kBucketsPerWeek, kCoefficientCount), dtype=float)
        kPiBucketConstant = np.pi / 2016.0
        for bucket in range(kBucketsPerWeek):
            for c in range(kCoefficientCount):
                self.table[bucket, c] = np.cos(kPiBucketConstant * (bucket + 0.5) * c)

    def get(self, bucket):
        return self.table[bucket]

def compress_speed_buckets(speeds):
    coefficients = np.zeros(kCoefficientCount, dtype=float)

    # DCT-II with speed normalization
    for bucket in range(kBucketsPerWeek):
        cos_values = BucketCosTable().get(bucket)
        coefficients += cos_values * speeds[bucket]

    coefficients[0] *= k1OverSqrt2

    result = np.round(kSpeedNormalization * coefficients).astype(np.int16)
    return result

def decompress_speed_bucket(coefficients, bucket_idx):
    cos_values = BucketCosTable().get(bucket_idx)

    # DCT-III with speed normalization
    speed = coefficients[0] * k1OverSqrt2
    for c, b in zip(coefficients[1:], cos_values[1:]):
        speed += c * b

    return speed * kSpeedNormalization

def encode_compressed_speeds(coefficients):
    result = bytearray()
    for coef in coefficients:
        # Convert to big endian
        result.extend(struct.pack('>h', coef))
    return base64.b64encode(result).decode()

def decode_compressed_speeds(encoded):
    decoded_str = base64.b64decode(encoded)
    if len(decoded_str) != kDecodedSpeedSize:
        raise ValueError(f"Decoded speed string size expected= {kDecodedSpeedSize} actual={len(decoded_str)}")

    coefficients = np.zeros(kCoefficientCount, dtype=np.int16)
    for i in range(kCoefficientCount):
        coefficients[i] = struct.unpack('<h', decoded_str[i*2:(i+1)*2])[0]  # Convert from big endian to little endian

    return coefficients
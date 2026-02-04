import math

FREQ = 44100  # sample rate
AMPLITUDE = int(32767 * 0.5)
TIME_PER_BIT = 300
BIT_FREQ = 440

WAKE_PATTERN = 0xD5AA  # 1101010110101010 in binary (16 bits), computed as the best (most unique) wake pattern for 16 bits
VALUE_ONE = 1.3
VALUE_TWO = 0.8


# ---- convert end values to binary (two's complement Q7.8 format) ----
FRACTION_BITS = 8
SCALE = 1 << FRACTION_BITS

MIN_INT = -32768
MAX_INT = 32767


def float_to_q7_8(x: float) -> int:
    # scale and round to nearest fixed point integer
    fixed = int(round(x * SCALE))

    # saturate to int16 range
    if fixed > MAX_INT:
        fixed = MAX_INT
    elif fixed < MIN_INT:
        fixed = MIN_INT

    # return as unsigned 16 bit value
    return fixed & 0xFFFF


# pack two 16 bit values into one 32 bit word
DATA_32 = (float_to_q7_8(VALUE_ONE) << 16) | float_to_q7_8(VALUE_TWO)

print(f"DATA_32 = 0x{DATA_32:08X}")
print(f"DATA_32 (bin) = {DATA_32:032b}")

# example of the decoding procedure
# def q7_8_to_float(value: int) -> float:
#     # interpret unsigned 16-bit as signed int16
#     if value & 0x8000:
#         value -= 0x10000

#     return value / SCALE


# def unpack_data_32(data32: int) -> tuple[float, float]:
#     # extract raw 16-bit values
#     raw_x = (data32 >> 16) & 0xFFFF
#     raw_y = data32 & 0xFFFF

#     # convert from Q7.8 to float
#     x = q7_8_to_float(raw_x)
#     y = q7_8_to_float(raw_y)

#     return x, y


# print(unpack_data_32(DATA_32))


def build_frame(wake, data32):
    """
    Frame layout:
    [ 8 bits wake ][ 32 bits data ][ 16 bits XOR checksum ]
    """
    checksum = ((data32 >> 16) ^ (data32 & 0xFFFF)) & 0xFFFF

    return wake.to_bytes(2, "big") + data32.to_bytes(4, "big") + checksum.to_bytes(2, "big")


def main():
    global BIT_FREQ

    frame = build_frame(WAKE_PATTERN, DATA_32)

    samples_per_bit = int(FREQ * TIME_PER_BIT / 1000)
    total_bits = len(frame) * 8
    total_samples = samples_per_bit * total_bits

    data = bytearray()

    # --- RIFF header ---
    data.extend(b"RIFF")
    data.extend((36 + total_samples * 2).to_bytes(4, "little"))
    data.extend(b"WAVE")
    data.extend(b"fmt ")
    data.extend((16).to_bytes(4, "little"))  # PCM
    data.extend((1).to_bytes(2, "little"))  # AudioFormat
    data.extend((1).to_bytes(2, "little"))  # Mono
    data.extend(FREQ.to_bytes(4, "little"))
    data.extend((FREQ * 2).to_bytes(4, "little"))
    data.extend((2).to_bytes(2, "little"))
    data.extend((16).to_bytes(2, "little"))
    data.extend(b"data")
    data.extend((total_samples * 2).to_bytes(4, "little"))

    # --- Audio data ---
    phase = 0.0
    phase_step = math.tau * BIT_FREQ / FREQ

    for byte in frame:
        for bit_index in range(7, -1, -1):
            bit = (byte >> bit_index) & 1

            for _ in range(samples_per_bit):
                if bit == 1:
                    value = int(AMPLITUDE * math.sin(phase))
                    phase += phase_step
                    if phase >= math.tau:
                        phase -= math.tau
                else:
                    value = 0

                data.extend(value.to_bytes(2, "little", signed=True))

    with open("./src/desktop_app/preview.wav", "wb") as f:
        f.write(data)

    print(
        f"Saved preview.wav | "
        f"{total_bits} bits | "
        f"wake=0x{WAKE_PATTERN:04X} "
        f"data=0x{DATA_32:08X}"
    )
    print("Frame bits:")
    print("".join(f"{byte:08b}" for byte in frame))


if __name__ == "__main__":
    main()

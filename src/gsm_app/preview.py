import math

FREQ = 44100  # sample rate
AMPLITUDE = int(32767 * 0.5)
TIME_PER_BIT = 0.05
BIT_FREQ = 1000

WAKE_PATTERN = 0b10101010  # 8 bits (10101010)
DATA_32 = 0b01010110110111010101100110011101  # 32 bits payload (mss meer in de toekomst idk)


def build_frame(wake, data32):
    """
    Frame layout:
    [ 8 bits wake ][ 32 bits data ][ 16 bits XOR checksum ]
    """

    checksum = ((data32 >> 16) ^ (data32 & 0xFFFF)) & 0xFFFF

    return wake.to_bytes(1, "big") + data32.to_bytes(4, "big") + checksum.to_bytes(2, "big")


def main():
    frame = build_frame(WAKE_PATTERN, DATA_32)

    samples_per_bit = int(FREQ * TIME_PER_BIT)
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

    with open("./src/gsm_app/preview.wav", "wb") as f:
        f.write(data)

    print(f"Saved preview.wav | " f"{total_bits} bits | " f"wake=0x{WAKE_PATTERN:02X} " f"data=0x{DATA_32:08X}")
    print("".join(f"{byte:08b}" for byte in frame))


if __name__ == "__main__":
    main()

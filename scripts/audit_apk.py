#!/usr/bin/env python3
"""Inspect the packaged native libraries, including all precompiled dependencies."""
import argparse
import struct
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("apk")
    args = parser.parse_args()
    failures = []
    count = 0
    with zipfile.ZipFile(args.apk) as archive:
        if archive.testzip() is not None:
            raise SystemExit("APK ZIP integrity failure")
        for name in archive.namelist():
            if not name.startswith("lib/") or not name.endswith(".so"):
                continue
            data = archive.read(name)
            if data[:6] != b"\x7fELF\x02\x01":
                failures.append(f"{name}: expected ELF64 little endian")
                continue
            if struct.unpack_from("<H", data, 18)[0] != 183 or not name.startswith("lib/arm64-v8a/"):
                failures.append(f"{name}: expected AArch64")
            phoff = struct.unpack_from("<Q", data, 32)[0]
            phsize, phcount = struct.unpack_from("<HH", data, 54)
            loads = 0
            for i in range(phcount):
                kind, flags, offset, vaddr, paddr, filesz, memsz, align = struct.unpack_from(
                    "<IIQQQQQQ", data, phoff + i * phsize)
                if kind == 1:
                    loads += 1
                    if align < 16384 or offset % 16384 != vaddr % 16384:
                        failures.append(f"{name}: LOAD alignment {align}")
            if not loads:
                failures.append(f"{name}: no LOAD segment")
            count += 1
    if not count:
        failures.append("No native libraries in APK")
    print(f"Checked {count} native libraries for AArch64 and 16 KB ELF compatibility")
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()

from pathlib import Path
import plistlib
import shutil


resources = Path(__file__).resolve().parents[1] / "Resources"
codec = resources / "ALC256"
codec_info = codec / "Info.plist"
pin_info = resources / "PinConfigs.kext" / "Contents" / "Info.plist"
layout_id = 26
codec_id = 0x10EC0256

codec_plist = plistlib.loads(codec_info.read_bytes())
pin_plist = plistlib.loads(pin_info.read_bytes())
personality = pin_plist["IOKitPersonalities"]["as.vit9696.AppleALC"]

if codec_plist["CodecID"] != codec_id & 0xFFFF:
    raise SystemExit("Unexpected codec ID in the ALC256 resource directory")

for kind in ("Layouts", "Platforms"):
    matches = [entry for entry in codec_plist["Files"][kind] if entry["Id"] == layout_id]
    if len(matches) != 1 or "X1605VA" not in matches[0].get("Comment", ""):
        raise SystemExit(f"Expected exactly one X1605VA layout {layout_id} in {kind}")
    codec_plist["Files"][kind] = matches

pins = [
    entry for entry in personality["HDAConfigDefault"]
    if entry["CodecID"] == codec_id and entry["LayoutID"] == layout_id
]
if len(pins) != 1 or "X1605VA" not in pins[0].get("Codec", ""):
    raise SystemExit("Expected exactly one X1605VA pin configuration")
personality["HDAConfigDefault"] = pins

keep = {codec_info.name}
for entries in codec_plist["Files"].values():
    for entry in entries:
        path = Path(entry["Path"])
        candidates = {path.name, path.with_suffix("").name}
        if not any((codec / name).is_file() for name in candidates):
            raise SystemExit(f"Missing resource {path}")
        keep.update(candidates)

codec_info.write_bytes(plistlib.dumps(codec_plist, sort_keys=False))
pin_info.write_bytes(plistlib.dumps(pin_plist, sort_keys=False))

for directory in resources.iterdir():
    if directory != codec and (directory / "Info.plist").is_file():
        shutil.rmtree(directory)

for file in codec.iterdir():
    if file.is_file() and file.name not in keep:
        file.unlink()

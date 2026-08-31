import csv
import os
from datetime import datetime

try:
    from PIL import Image
except Exception:
    Image = None

IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'images')
IMAGES_DIR = os.path.normpath(IMAGES_DIR)

out_csv = os.path.join(os.path.dirname(__file__), '..', 'images_exif.csv')
out_md = os.path.join(os.path.dirname(__file__), '..', 'images_catalog.md')

def get_exif(path):
    data = {}
    if not Image:
        return data
    try:
        with Image.open(path) as img:
            info = getattr(img, '_getexif', lambda: None)()
            if info:
                for k, v in info.items():
                    data[str(k)] = str(v)
            # also include PNG info dict if present
            for k, v in getattr(img, 'info', {}).items():
                data[str(k)] = str(v)
    except Exception:
        pass
    return data

rows = []
catalog_lines = ['# Image catalog\n']

for root, dirs, files in os.walk(IMAGES_DIR):
    for fn in sorted(files):
        path = os.path.join(root, fn)
        rel = os.path.relpath(path, os.path.dirname(__file__) + '\\..')
        try:
            st = os.stat(path)
            size = st.st_size
            mtime = datetime.fromtimestamp(st.st_mtime).isoformat()
        except Exception:
            size = ''
            mtime = ''
        exif = get_exif(path)
        exif_keys = ';'.join(sorted(exif.keys()))
        rows.append({'filename': fn, 'path': path, 'size': size, 'mtime': mtime, 'exif_keys': exif_keys})

        # provisional caption and flags
        caption = 'Provisional caption: verify provenance.'
        flags = []
        lname = fn.lower()
        if lname.startswith('img_') or lname.startswith('screenshot') or 'google' in lname:
            flags.append('possible-screenshot')
        if lname.startswith('img_'):
            flags.append('device-photo')
        if fn.lower().endswith(('.png', '.jpg', '.jpeg')) and 'img_' in fn.lower():
            flags.append('review-for-identifiability')

        catalog_lines.append(f'## {fn}\n')
        catalog_lines.append(f'- Path: {rel}\n')
        catalog_lines.append(f'- Size: {size} bytes\n')
        catalog_lines.append(f'- Modified: {mtime}\n')
        catalog_lines.append(f'- EXIF keys: {exif_keys or "(none)"}\n')
        catalog_lines.append(f'- Caption: {caption}\n')
        if flags:
            catalog_lines.append(f'- Flags: {", ".join(flags)}\n')
        catalog_lines.append('\n')

with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['filename', 'path', 'size', 'mtime', 'exif_keys'])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

with open(out_md, 'w', encoding='utf-8') as f:
    f.writelines([l + '\n' if not l.endswith('\n') else l for l in catalog_lines])

print('Wrote', out_csv)
print('Wrote', out_md)

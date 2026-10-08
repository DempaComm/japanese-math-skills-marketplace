"""Build a public archive from an explicit allowlist; never include local cases."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ['README.md', 'LICENSE.md', 'ATTRIBUTION.md', 'VERSION', '検索.command',
         'publication/inventory.json', 'publication/inventory.md',
         'publication/collection-policy.md', 'publication/validation.md',
         'viewer/build.py', 'viewer/serve.py', 'viewer/tests/purpose-filter.cjs',
         'scripts/build_release.py']
DIRS = ['skills', 'LICENSES', 'viewer/dist']

def main():
    paths = {ROOT / name for name in FILES}
    for name in DIRS:
        paths.update(p for p in (ROOT / name).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc')
    payload = {}
    for p in sorted(paths):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_symlink() or not p.is_file():
            raise ValueError(f'Unexpected release input: {rel}')
        data = p.read_bytes()
        # Keep source TeX unchanged; scan every shipped file for private artifacts.
        for marker in (b'/Users/', b'/private/var/', b'local-case-studies/', b'.codex/sessions/'):
            if marker in data and rel != 'scripts/build_release.py':
                raise ValueError(f'Private reference in {rel}: {marker!r}')
        if rel != 'scripts/build_release.py' and re.search(''.join(chr(c) for c in [20234,25975,124,21916,26007,124,121,111,115,104,105,116,111,124,105,115,104,105,107,105]), data.decode('utf-8', errors='replace'), re.I):
            raise ValueError(f'Personal identifier in {rel}')
        payload[rel] = data
    # Local Markdown links must resolve inside the selected payload.
    for rel, data in payload.items():
        if not rel.endswith('.md'):
            continue
        for target in re.findall(r'\]\(([^)]+)\)', data.decode()):
            target = target.split('#')[0]
            if not target or '://' in target or target.startswith('mailto:'):
                continue
            resolved = (ROOT / rel).parent.joinpath(target).resolve()
            key = resolved.relative_to(ROOT).as_posix()
            if key not in payload:
                raise ValueError(f'Broken release link: {rel} -> {target}')
    manifest = {k: hashlib.sha256(v).hexdigest() for k, v in payload.items()}
    payload['release-manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode()
    version = (ROOT/'VERSION').read_text().strip()
    out = ROOT/'releases'
    out.mkdir(exist_ok=True)
    archive = out/f'japanese-math-skills-{version}.zip'
    prefix = f'japanese-math-skills-{version}/'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for rel, data in sorted(payload.items()):
            info = zipfile.ZipInfo(prefix+rel, (2026, 9, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if rel.endswith('.command') else 0o100644) << 16
            z.writestr(info, data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for rel, data in payload.items():
            assert z.read(prefix+rel) == data
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    print(f'{archive}: {len(payload)} files, {archive.stat().st_size:,} bytes; links and round trip verified')

if __name__ == '__main__':
    main()

# Local Naming Standard

## Core rules
- Use lowercase `kebab-case` for folders, repo roots, scripts, and most files.
- Use only letters, numbers, and hyphens in names where possible.
- Use `YYYY-MM-DD` for date prefixes in dated files.
- Use short business slugs only: `mna`, `tga`, `tgah`, `shl`, `personal`.
- Avoid placeholders like `my-project`, `misc`, `final-v2`, `copy`, `new`.

## Folder model
- Top-level business roots live under `businesses/`.
- Each business uses PARA internally:
  - `projects/`
  - `areas/`
  - `resources/`
  - `archive/`

## Exceptions
- Keep vendor-mandated names when exact naming is required.
- Keep externally shared client-facing names unchanged if renaming would break expectations.

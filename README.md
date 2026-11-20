# The World in Four Frames — 20 November 2026

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/moonku-ai/news-image-20261120-v3/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/moonku-ai/news-image-20261120-v3/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A one-image summary of Friday 20 November 2026's world news, built for the
[make.fun](https://make.fun/bounty/news-image-20261120) news-image bounty.
Four large pictogram frames — Cyclone Akvan's landfall in Odisha, the ICJ's
9–6 genocide verdict against Myanmar, Anthropic's stock-market debut, and
ballistic missiles hitting Kyiv — plus an "also today" ticker covering the
Hormuz tanker mine, the Genoa drone shutdown, the Houthi strikes, Seoul's
retrial order, the Trump–Xi–Putin Peace Declaration, the Nvidia probe, the
Pete Rose pardon and the Sensex.

## Run

```sh
python3 main.py            # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=out python3 main.py
python3 -m unittest test_main -v
```

Pure Python standard library only — no third-party packages, no network.
The program is deterministic: two runs write byte-identical PNGs
(1024×1024, under 1 MiB).

## License

MIT — see [LICENSE](LICENSE). SPDX-License-Identifier: MIT.

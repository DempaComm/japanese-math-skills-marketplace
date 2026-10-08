# DempaComm Skills Marketplace

English | [日本語](README.md)

A GitHub-backed Codex marketplace for DempaComm's Japanese mathematics-writing
and independent exposition-review skills. The marketplace identifier is
`dempacomm`, displayed as **DempaComm**.

## Install

With a Codex CLI that supports `codex plugin`, run:

```sh
codex plugin marketplace add DempaComm/japanese-math-skills-marketplace
codex plugin add japanese-math-skills@dempacomm
```

Start a new chat after installation. In a supported app, choose **DempaComm** in
the plugin directory and install **Japanese Math Skills**. Refresh or restart
the app if the added marketplace has not appeared.

```sh
codex plugin marketplace list
codex plugin list --marketplace dempacomm --json
```

## Included plugin

`japanese-math-skills` version **0.1.1** installs both skills together:

| Skill | Purpose |
| --- | --- |
| `write-japanese-math` | Draft, revise, and polish Japanese mathematics papers, exposition, and lecture notes |
| `read-japanese-math` | Explicitly delegated independent exposition review of a frozen Japanese manuscript |

The package preserves the reader's relative references to the writer's shared
guidance. It includes the public corpus of 179 TeX files, source records and
hashes, contextual examples, and search tools. Corpus search needs **Python
3.10 or later**, with no additional Python packages. Typesetting a manuscript
uses its host project's TeX environment. See the bundled
[skill guide](plugins/japanese-math-skills/README.md).

## Update

```sh
codex plugin marketplace upgrade dempacomm
codex plugin add japanese-math-skills@dempacomm
```

Marketplace versions are snapshots of a published source commit. They do not
automatically follow changes in the source repository.

## Source and license

The source is [DempaComm/japanese-math-skills](https://github.com/DempaComm/japanese-math-skills)
at public commit `ae806c56fff2c8edaad307cec9e22c9ad6900baf`.
[UPSTREAM.json](UPSTREAM.json) records the revision, Git blob identities, and
SHA-256 hashes. All 237 imported files are preserved byte for byte; the plugin
manifest and icon are additions. Local revision cases, chat history, and
machine-specific configuration are excluded.

The CC BY 4.0 and inherited upstream MIT notices are retained. See the
[license](LICENSE.md) and [source attribution](plugins/japanese-math-skills/ATTRIBUTION.md).

This is a repository marketplace. It has not been submitted to OpenAI's public
plugin directory. See the [official OpenAI documentation](https://developers.openai.com/plugins/build/plugins)
and [submission guide](https://developers.openai.com/plugins/deploy/submission).

## Validate

```sh
python3 tools/validate.py
python3 -m unittest discover -s plugins/japanese-math-skills/skills/write-japanese-math/scripts/tests -v
python3 plugins/japanese-math-skills/skills/write-japanese-math/scripts/corpus.py --verify
python3 plugins/japanese-math-skills/skills/write-japanese-math/scripts/rebuild_corpus.py --check
node plugins/japanese-math-skills/viewer/tests/purpose-filter.cjs
```

These checks cover metadata, relative references, source integrity, corpus
hashes, and search/classification behavior. The last command needs Node.js and
checks viewer logic; it is not a browser or visual inspection. These checks do
not certify mathematical proofs.

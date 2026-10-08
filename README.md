# DempaComm Skills Marketplace

[English](README.en.md) | 日本語

DempaComm の日本語数学文書用スキルを、一括導入するための Codex marketplace です。
一覧の表示名は **DempaComm**、識別子は `dempacomm` です。

## 導入

`codex plugin` に対応する Codex CLI で、次を実行します。

```sh
codex plugin marketplace add DempaComm/japanese-math-skills-marketplace
codex plugin add japanese-math-skills@dempacomm
```

導入後は新しいチャットを開始してください。対応するアプリのプラグイン一覧で
**DempaComm** を選び、**Japanese Math Skills** をインストールすることもできます。
追加した marketplace が表示されない場合は、アプリを更新または再起動してください。

登録・導入状態は次のコマンドで確認できます。

```sh
codex plugin marketplace list
codex plugin list --marketplace dempacomm --json
```

## 収録内容

プラグイン `japanese-math-skills` **0.1.1** に、次の2スキルを同梱しています。

| スキル | 用途 |
| --- | --- |
| `write-japanese-math` | 日本語の数学論文・解説・講義ノートの執筆、改稿、推敲 |
| `read-japanese-math` | 明示的に委任された、凍結原稿の独立した文章レビュー |

2スキルの相対参照を保持しているため、個別にフォルダを配置する必要はありません。
公開版の179 TeXファイル、出典・ハッシュ、文脈付き用例、検索ツールも含めています。
検索には **Python 3.10以上**が必要で、追加Pythonパッケージは不要です。
実際の原稿の組版には、そのプロジェクトのTeX環境を使います。
使い方と用例コーパスについては、同梱した[スキルの案内](plugins/japanese-math-skills/README.md)を参照してください。

## 更新

```sh
codex plugin marketplace upgrade dempacomm
codex plugin add japanese-math-skills@dempacomm
```

配布版は公開コミットから作成したスナップショットです。取得元の変更は
自動反映されません。更新前に版番号と取得コミットを確認してください。

## 出典とライセンス

取得元は [DempaComm/japanese-math-skills](https://github.com/DempaComm/japanese-math-skills)
の公開コミット `ae806c56fff2c8edaad307cec9e22c9ad6900baf`です。
[UPSTREAM.json](UPSTREAM.json)に取得コミット、Git blob の識別子、SHA-256を記録し、
公開済みの237ファイルを無改変で同梱しています。プラグイン定義とアイコンを追加しました。

収録原文・日本語版・コーパスのCC BY 4.0表示と、元の英語スキルのMIT表示を保持しています。
[ライセンス](LICENSE.md)、[元の出典表示](plugins/japanese-math-skills/ATTRIBUTION.md)を参照してください。
ローカルの改稿事例、会話履歴、作業環境の設定は含めていません。

これは GitHub リポジトリを登録して使う marketplace です。OpenAI公式の一般公開
一覧への申請は行っていません。[公式OpenAIドキュメント](https://developers.openai.com/plugins/build/plugins)
と[公開申請の案内](https://developers.openai.com/plugins/deploy/submission)を参照してください。

## 検査

```sh
python3 tools/validate.py
python3 -m unittest discover -s plugins/japanese-math-skills/skills/write-japanese-math/scripts/tests -v
python3 plugins/japanese-math-skills/skills/write-japanese-math/scripts/corpus.py --verify
python3 plugins/japanese-math-skills/skills/write-japanese-math/scripts/rebuild_corpus.py --check
node plugins/japanese-math-skills/viewer/tests/purpose-filter.cjs
```

定義、相対参照、原本との一致、出典ハッシュ、検索・分類の動作を確認します。
最後のコマンドはNode.jsで行う検索画面のロジック検査です。
ブラウザの実操作・表示の検査や、数学的証明の検証ではありません。

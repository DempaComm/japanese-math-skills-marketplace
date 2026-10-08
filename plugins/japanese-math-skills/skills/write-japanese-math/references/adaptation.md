# 既存スキルからの適応

2026年9月14日に現行の write-research-paper / read-research-paper を参照した。
[upstream-manifest.json](upstream-manifest.json) に参照ファイルのハッシュを記録した。
日本語版は独立したスキルとして保守し、英語版の自動追従や完全な逐語訳とはしない。

|元の要素|日本語版|扱い|
|---|---|---|
|write-research-paper|write-japanese-math|通常の執筆・推敲、範囲維持を翻訳・整理|
|paper-writing|paper-writing.md|数学的説明基準を翻訳・圧縮、短い解説への構成強制を緩和|
|author-style|japanese-style.md / interfaces.md / tex.md|言語に依存しない論理・参照規則を継承|
|corpus-style / lexicon|corpus-method.md / lexicon.md|指定サイトの日本語TeXに入れ替え|
|workflow / owner-proof-decisions|workflow.md / proof-detail.md|委任境界、原判定保持、承認済み省略を継承|
|read-research-paper|read-japanese-math|逐次・全体編集・差分の役割と隔離を日本語で実装|

英語の give/suppose 制限は日本語の禁止語へ変換しない。句読点と主語省略は日本語の既定を設けた。
英語版の厳密なソース改行、概要一行化、文献方式・リンク色の一律指定は、日本語版では既存組版の保持を優先する。
AI利用記載は実際の利用内容と確認済みの事実だけを書く。著者による証明確認を推測して宣言しない。

コーパスの文章は歴史的な用例であり現行の命令ではない。
数学本文の役割に使える表現と、ブログの語り口・私的なコメントを分離する。
全文書の証明を検証したり、頻出語を著者の絶対規則にしたりするものではない。

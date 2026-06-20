# 日本国憲法成立RAG デモ用評価クエリ集

このファイルは、デモでそのまま使える評価用クエリ集である。各クエリについて、主にヒットしてほしいファイルと確認ポイントを付した。評価では、まず `top-3` 以内に期待ファイルが入るかを見て、その後に生成された回答が確認ポイントを満たすかを確認すると扱いやすい。

## 使い方

- 検索だけを見る場合: `query` と `expected_primary_files` を使う
- 回答生成まで見る場合: `checkpoints` も使う
- デモでは、日付検索、論点検索、比較検索、条文検索を順に混ぜると分かりやすい

---

## 1. 全体像把握

### Q01
- query: `日本国憲法の成立過程を全体像で説明して`
- expected_primary_files:
  - `overview_constitution_birth.md`
  - `timeline_1945_1947.md`
- checkpoints:
  - 1946年2月13日を転換点として説明できる
  - 日本側調査とGHQ草案提示後の二段階に分けられる

### Q02
- query: `日本国憲法の誕生は押し付けか自主制定か`
- expected_primary_files:
  - `overview_constitution_birth.md`
  - `chapter3_ghq_draft_and_government_response.md`
  - `chapter4_imperial_diet_deliberation.md`
- checkpoints:
  - GHQの関与と日本側の修正・審議の両方に触れる

### Q03
- query: `日本国憲法成立の重要な転換点はいつですか`
- expected_primary_files:
  - `overview_constitution_birth.md`
  - `timeline_1945_1947.md`
  - `chapter3_ghq_draft_and_government_response.md`
- checkpoints:
  - 1946-02-13 を挙げる
  - GHQ草案手交の意味を説明できる

### Q04
- query: `公布と施行の違いを日本国憲法の事例で説明して`
- expected_primary_files:
  - `chapter5_enforcement.md`
  - `constitution_original_national_archives.md`
  - `constitution_text_current_egov.md`
- checkpoints:
  - 公布 1946-11-03
  - 施行 1947-05-03

### Q05
- query: `日本国憲法の成立で外からの力と内からの力とは何ですか`
- expected_primary_files:
  - `overview_constitution_birth.md`
  - `chapter1_war_end_and_revision_start.md`
- checkpoints:
  - 占領改革の圧力
  - 戦前体制の限界と国内の民主化要求

---

## 2. 日付検索

### Q06
- query: `1945年7月26日に何が起きた`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter1_war_end_and_revision_start.md`
- checkpoints:
  - ポツダム宣言発表

### Q07
- query: `1945年10月4日に何があった`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter1_war_end_and_revision_start.md`
- checkpoints:
  - 自由の指令
  - 近衛文麿への憲法改正示唆

### Q08
- query: `1945年10月25日に設置された委員会は`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter1_war_end_and_revision_start.md`
  - `chapter2_matsumoto_committee_and_private_drafts.md`
- checkpoints:
  - 憲法問題調査委員会
  - 松本委員会

### Q09
- query: `1945年12月26日に発表された民間草案は何`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter2_matsumoto_committee_and_private_drafts.md`
- checkpoints:
  - 憲法研究会の憲法草案要綱

### Q10
- query: `1946年2月1日のスクープは何だった`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter3_ghq_draft_and_government_response.md`
- checkpoints:
  - 毎日新聞による松本委員会試案のスクープ

### Q11
- query: `1946年2月3日に示された三原則とは`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter3_ghq_draft_and_government_response.md`
  - `issue_popular_sovereignty_and_emperor.md`
  - `issue_renunciation_of_war.md`
- checkpoints:
  - マッカーサー三原則
  - 天皇、戦争放棄、封建制度の撤廃

### Q12
- query: `1946年2月8日に日本政府は何を提出した`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter2_matsumoto_committee_and_private_drafts.md`
  - `chapter3_ghq_draft_and_government_response.md`
- checkpoints:
  - 憲法改正要綱

### Q13
- query: `1946年2月13日に何が起きた`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter3_ghq_draft_and_government_response.md`
- checkpoints:
  - GHQが日本側要綱を拒否
  - GHQ草案を手交

### Q14
- query: `1946年3月6日に発表されたものは`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter3_ghq_draft_and_government_response.md`
- checkpoints:
  - 憲法改正草案要綱

### Q15
- query: `1946年4月17日に公表された草案は`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter3_ghq_draft_and_government_response.md`
- checkpoints:
  - ひらがな口語体の憲法改正草案

### Q16
- query: `1946年6月20日は制定過程でどんな日か`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter4_imperial_diet_deliberation.md`
- checkpoints:
  - 帝国議会へ改正案提出

### Q17
- query: `1946年8月24日に衆議院で何が決まった`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter4_imperial_diet_deliberation.md`
- checkpoints:
  - 修正案可決
  - 賛成421、反対8

### Q18
- query: `1946年10月6日に貴族院で何が起きた`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter4_imperial_diet_deliberation.md`
- checkpoints:
  - 貴族院が修正可決

### Q19
- query: `1946年11月3日に何があった`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter4_imperial_diet_deliberation.md`
  - `constitution_original_national_archives.md`
- checkpoints:
  - 日本国憲法公布

### Q20
- query: `1947年5月3日に何が施行された`
- expected_primary_files:
  - `timeline_1945_1947.md`
  - `chapter5_enforcement.md`
  - `constitution_text_current_egov.md`
- checkpoints:
  - 日本国憲法施行

---

## 3. 人物検索

### Q21
- query: `松本烝治は制定過程で何をした人か`
- expected_primary_files:
  - `chapter2_matsumoto_committee_and_private_drafts.md`
  - `chapter3_ghq_draft_and_government_response.md`
- checkpoints:
  - 松本委員会委員長
  - 松本四原則
  - 2月8日提出案

### Q22
- query: `近衛文麿の憲法改正調査とは何か`
- expected_primary_files:
  - `chapter1_war_end_and_revision_start.md`
  - `chapter2_matsumoto_committee_and_private_drafts.md`
- checkpoints:
  - 内大臣府での調査
  - 1945年11月の奉答

### Q23
- query: `佐々木惣一はどの草案に関わったか`
- expected_primary_files:
  - `chapter1_war_end_and_revision_start.md`
  - `chapter2_matsumoto_committee_and_private_drafts.md`
- checkpoints:
  - 近衛調査への協力
  - 帝国憲法改正ノ必要

### Q24
- query: `金森徳次郎の役割を説明して`
- expected_primary_files:
  - `chapter4_imperial_diet_deliberation.md`
  - `constitution_original_national_archives.md`
- checkpoints:
  - 憲法担当国務大臣
  - 帝国議会で答弁

### Q25
- query: `入江俊郎と佐藤達夫は何を担当したか`
- expected_primary_files:
  - `chapter3_ghq_draft_and_government_response.md`
  - `chapter1_war_end_and_revision_start.md`
- checkpoints:
  - 3月2日案以降の政府案起草中心

### Q26
- query: `芦田均はどの修正で有名か`
- expected_primary_files:
  - `chapter4_imperial_diet_deliberation.md`
  - `issue_renunciation_of_war.md`
- checkpoints:
  - 芦田修正
  - 第9条2項冒頭の修正

### Q27
- query: `ホイットニーは2月13日に何をした`
- expected_primary_files:
  - `chapter3_ghq_draft_and_government_response.md`
  - `timeline_1945_1947.md`
- checkpoints:
  - 日本側要綱拒否
  - GHQ草案手交

---

## 4. 論点検索

### Q28
- query: `国民主権と天皇制はどう両立させたのか`
- expected_primary_files:
  - `issue_popular_sovereignty_and_emperor.md`
  - `constitution_text_current_egov.md`
- checkpoints:
  - 主権は国民に存する
  - 天皇は象徴

### Q29
- query: `国体護持とは制定過程でどういう意味だったのか`
- expected_primary_files:
  - `issue_popular_sovereignty_and_emperor.md`
  - `chapter1_war_end_and_revision_start.md`
- checkpoints:
  - 天皇の地位維持要求
  - 受諾交渉との関係

### Q30
- query: `象徴天皇制はどのように作られたのか`
- expected_primary_files:
  - `issue_popular_sovereignty_and_emperor.md`
  - `chapter3_ghq_draft_and_government_response.md`
- checkpoints:
  - GHQ草案
  - 第1条修正

### Q31
- query: `第9条はなぜ入ったのか`
- expected_primary_files:
  - `issue_renunciation_of_war.md`
  - `chapter3_ghq_draft_and_government_response.md`
- checkpoints:
  - 非軍事化
  - マッカーサー・ノート

### Q32
- query: `芦田修正とは何か`
- expected_primary_files:
  - `issue_renunciation_of_war.md`
  - `chapter4_imperial_diet_deliberation.md`
- checkpoints:
  - 前項の目的を達するため
  - 衆議院小委員会

### Q33
- query: `基本的人権の保障で明治憲法と何が変わったか`
- expected_primary_files:
  - `issue_human_rights.md`
  - `constitution_text_current_egov.md`
- checkpoints:
  - 法律ノ範囲内からの転換
  - 公共の福祉

### Q34
- query: `第24条は制定過程でなぜ重要か`
- expected_primary_files:
  - `issue_human_rights.md`
  - `constitution_text_current_egov.md`
- checkpoints:
  - 個人の尊厳
  - 両性の本質的平等

### Q35
- query: `社会権はいつどのように入ったのか`
- expected_primary_files:
  - `issue_human_rights.md`
  - `chapter4_imperial_diet_deliberation.md`
- checkpoints:
  - 生存権
  - 勤労権
  - 衆議院での追加

### Q36
- query: `外国人の人権は制定時にどう扱われたか`
- expected_primary_files:
  - `issue_human_rights.md`
- checkpoints:
  - 何人と国民の使い分け

### Q37
- query: `新しい二院制議会はなぜ採用されたのか`
- expected_primary_files:
  - `issue_bicameral_system.md`
  - `chapter4_imperial_diet_deliberation.md`
- checkpoints:
  - 一院制案との比較
  - 安定性と継続性の議論

### Q38
- query: `参議院は旧貴族院と何が違うのか`
- expected_primary_files:
  - `issue_bicameral_system.md`
  - `constitution_text_current_egov.md`
- checkpoints:
  - 公選議員
  - 全国民代表原理

---

## 5. 比較検索

### Q39
- query: `松本委員会案と憲法研究会案の違いは`
- expected_primary_files:
  - `chapter2_matsumoto_committee_and_private_drafts.md`
  - `draft_comparison_house_of_representatives.pdf`
- checkpoints:
  - 天皇主権維持か主権在民か
  - 天皇権能の違い

### Q40
- query: `GHQ草案以前の日本側案はどの程度保守的だったか`
- expected_primary_files:
  - `chapter2_matsumoto_committee_and_private_drafts.md`
  - `chapter3_ghq_draft_and_government_response.md`
  - `draft_comparison_house_of_representatives.pdf`
- checkpoints:
  - 松本案の性格
  - GHQ拒否の理由

### Q41
- query: `3月2日案とGHQ草案の違いは何か`
- expected_primary_files:
  - `chapter3_ghq_draft_and_government_response.md`
  - `issue_popular_sovereignty_and_emperor.md`
- checkpoints:
  - 前文の扱い
  - 国民主権表現の曖昧化

### Q42
- query: `4月17日草案と最終公布条文の違いを知りたい`
- expected_primary_files:
  - `chapter4_imperial_diet_deliberation.md`
  - `issue_renunciation_of_war.md`
  - `issue_popular_sovereignty_and_emperor.md`
- checkpoints:
  - 第9条
  - 第1条
  - 文民条項

### Q43
- query: `衆議院修正と貴族院修正の違いは`
- expected_primary_files:
  - `chapter4_imperial_diet_deliberation.md`
  - `constitution_process_overview_house_of_representatives.pdf`
- checkpoints:
  - 衆議院での芦田修正
  - 貴族院での文民条項

### Q44
- query: `公布後と施行後で何が変わったのか`
- expected_primary_files:
  - `chapter5_enforcement.md`
  - `constitution_original_national_archives.md`
- checkpoints:
  - 附属法整備
  - 新選挙と第1回国会

---

## 6. 条文検索

### Q45
- query: `日本国憲法第1条の内容を教えて`
- expected_primary_files:
  - `constitution_text_current_egov.md`
  - `issue_popular_sovereignty_and_emperor.md`
- checkpoints:
  - 象徴
  - 主権の存する日本国民の総意

### Q46
- query: `日本国憲法第9条の条文は`
- expected_primary_files:
  - `constitution_text_current_egov.md`
  - `issue_renunciation_of_war.md`
- checkpoints:
  - 第1項と第2項の両方

### Q47
- query: `日本国憲法第24条の条文を出して`
- expected_primary_files:
  - `constitution_text_current_egov.md`
  - `issue_human_rights.md`
- checkpoints:
  - 婚姻
  - 個人の尊厳
  - 両性の本質的平等

### Q48
- query: `日本国憲法第66条2項はどんな内容か`
- expected_primary_files:
  - `constitution_text_current_egov.md`
  - `chapter4_imperial_diet_deliberation.md`
- checkpoints:
  - 国務大臣は文民でなければならない

---

## 7. 原本・一次資料検索

### Q49
- query: `日本国憲法の御署名原本の請求番号は`
- expected_primary_files:
  - `constitution_original_national_archives.md`
- checkpoints:
  - 御30168100

### Q50
- query: `日本国憲法原本はどこで確認できる`
- expected_primary_files:
  - `constitution_original_national_archives.md`
- checkpoints:
  - 国立公文書館デジタルアーカイブ
  - 資料ページURL

---

## 最低限の採点基準

- `A`: 期待ファイルが `top-3` に入り、回答も主要チェックポイントを満たす
- `B`: 期待ファイルは `top-5` に入るが、回答に一部抜けがある
- `C`: 関連資料は拾うが、主資料に届かない
- `D`: 日付・人物・論点を取り違える

## デモで見せやすいおすすめ5問

- `1946年2月13日に何が起きた`
- `芦田修正とは何か`
- `国民主権と天皇制はどう両立させたのか`
- `公布と施行の違いを日本国憲法の事例で説明して`
- `日本国憲法の御署名原本の請求番号は`

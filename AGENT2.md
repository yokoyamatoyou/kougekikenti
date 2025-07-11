### **プロジェクト名：オールインワン誹謗中傷証拠収集ツール (v3.0 \- 高速並列処理対応)**

### **1\. プロジェクト概要**

#### **1.1. 開発目標 (Target State)**

既存の分析ツールを、\*\*データ収集から「高速な並列分析」までを一気通貫で行える、高性能な「オールインワン・ツール」\*\*に進化させる。大量の投稿データでも、現実的な時間内に処理を完了させることを最優先目標とする。

### **2\. 提案するディレクトリ構造**

保守性と拡張性を高めるため、以下のディレクトリ構造を採用する。

aggression\_analyzer/  
├── main.py                 \# アプリケーションのメインエントリーポイント  
├── requirements.txt        \# 依存ライブラリリスト  
├── .env.example            \# 環境変数設定のテンプレート  
├── .gitignore              \# Git管理対象外ファイル  
├── README.md               \# プロジェクトの説明書  
│  
├── config/  
│   └── settings.py         \# 設定ファイル（モデル名、プロンプト、並列処理数等）  
│  
├── gui/  
│   ├── \_\_init\_\_.py  
│   └── app.py              \# GUIアプリケーション本体のクラス  
│  
├── modules/  
│   ├── \_\_init\_\_.py  
│   ├── scraper.py          \# X(旧Twitter) スクレイピングモジュール  
│   └── analyzer.py         \# OpenAI 並列分析モジュール  
│  
└── output/                 \# 分析結果のExcelファイルを保存するデフォルトディレクトリ  
    └── .gitkeep

### **3\. AIエージェント向け 高詳細開発指示**

このプロジェクトは、以下のフェーズに分けて開発を進めること。各タスク完了後、指定された「検証ステップ」を実行し、進捗ログを更新すること。

### **【フェーズ0】 プロジェクトのセットアップと高度なリファクタリング**

**目的:** 既存コードを専門的な構造に整理し、堅牢性と保守性を向上させる。

* **タスク 0.1: ディレクトリとファイルの作成**  
  * 上記のディレクトリ構造案に基づき、必要なディレクトリと空のPythonファイルを作成する。  
* **タスク 0.2: 依存関係と環境変数の設定**  
  * requirements.txt を作成し、内容を記述する: openai, pandas, customtkinter, openpyxl, snscrape, python-dotenv。  
  * .env.example を作成し、OPENAI\_API\_KEY="YOUR\_API\_KEY\_HERE" と記述する。  
* **タスク 0.3: 設定ファイルの作成 (config/settings.py)**  
  * アプリケーション全体の設定をこのファイルで一元管理する。  
    \# config/settings.py  
    \# \--- OpenAI Models \---  
    MODERATION\_MODEL \= "text-moderation-latest"  
    AGGRESSION\_ANALYSIS\_MODEL \= "gpt-4o-mini"

    \# \--- Concurrency Settings \---  
    \# 同時に実行するAI分析の最大数。PCのスペックやAPIのレートリミットに応じて調整。  
    MAX\_CONCURRENT\_WORKERS \= 8

    \# \--- Analysis Parameters \---  
    \# (プロンプトやスコア重み付けなどをここに定義)

* **タスク 0.4: ロジックの分離とクラス化**  
  * 既存のコードを新しいディレクトリ構造に合わせて分離・クラス化する。  
    * **gui/app.py**: customtkinter関連のUIコードを ModerationApp クラスとしてここに移動。  
    * **modules/analyzer.py**: 分析ロジックを Analyzer クラスとしてここに移動。  
    * **main.py**: アプリケーションを起動する数行のコードのみを記述。  
* **【検証ステップ 0】**  
  * pip install \-r requirements.txt を実行。  
  * main.py を実行し、既存のExcelファイルを読み込んで分析する機能が、リファクタリング前と全く同じように動作することを確認する。

### **【フェーズ1】 データ収集モジュールの実装**

**目的:** X(旧Twitter)から投稿データをスクレイピングする機能を、安定性を重視して実装する。

* **タスク 1.1: スクレイパーモジュールの作成 (modules/scraper.py)**  
  * Scraper クラスを定義し、scrape\_user\_posts(self, username: str, limit: int) メソッドを実装する。  
  * **重要:** スクレイピングはX社のサーバーに直接アクセスするため、ブロックを避けることが最優先。**この処理は並列化せず、必ず直列で実行すること。** 1リクエストごとに短い待機時間を設ける。  
  * エラーハンドリングを実装し、ユーザーが存在しない場合などに対応する。  
* **【検証ステップ 1】**  
  * scraper.py を直接実行した際に、テスト用のユーザーIDで動作確認ができるよう、if \_\_name\_\_ \== "\_\_main\_\_": ブロックにテストコードを記述する。

### **【フェーズ2】 高速並列分析エンジンの実装**

**目的:** 収集した大量のデータを、並列処理によって高速に分析するエンジンを構築する。

* **タスク 2.1: Analyzerクラスの並列処理対応 (modules/analyzer.py)**  
  * concurrent.futures.ThreadPoolExecutor を利用して、分析処理を並列化する。  
  * 新しいメソッド analyze\_dataframe\_in\_parallel(self, df: pd.DataFrame) を実装する。  
  * **処理フロー:**  
    1. ThreadPoolExecutor を max\_workers=MAX\_CONCURRENT\_WORKERS で初期化する。  
    2. 入力されたDataFrameの各行に対して、分析タスク（Moderation API \+ GPT API呼び出し）を作成し、Executorに投入（submit）する。  
    3. 全てのタスクの完了を待ち、結果を収集する。  
    4. 分析結果を元のDataFrameに結合して返す。  
  * **GUI連携:** 進捗をリアルタイムにGUIへ伝えるため、タスク完了ごとにコールバック関数を呼び出す仕組みを実装する。  
* **タスク 2.2: GUIの非同期処理対応 (gui/app.py)**  
  * threading を利用し、収集と分析の全プロセスをバックグラウンドスレッドで実行する。これにより、処理中にUIが固まるのを防ぐ。  
  * バックグラウンドスレッドから、Analyzerのコールバック経由でプログレスバーとステータス表示を安全に更新する (self.after() を使用)。  
* **【検証ステップ 2】**  
  * 200件のダミーデータを作成し、analyze\_dataframe\_in\_parallel を実行する。  
  * 直列処理の場合と比較して、処理時間が大幅に短縮されることを確認する。  
  * アプリケーションを起動し、大量のデータを処理させてもUIがフリーズしないことを確認する。

### **【フェーズ3】 最終化とドキュメント整備**

**目的:** ツールの完成度を高め、高品質なドキュメントを作成する。

* **タスク 3.1: コードのクリーンアップと型ヒントの追加**  
  * プロジェクト全体のコードにPythonの型ヒントを追加し、可読性と保守性を向上させる。  
* **タスク 3.2: README.md の作成**  
  * プロジェクトの目的、新しいアーキテクチャの概要、セットアップ方法、使い方を詳細に記述する。  
  * MAX\_CONCURRENT\_WORKERS のような重要な設定項目について、調整方法の説明を加える。  
* **【検証ステップ 3】**  
  * README.md の指示のみを頼りに、クリーンな環境でプロジェクトのセットアップと実行が問題なく行えることを確認する。

### **AIエージェント進捗ログ (AI Agent Progress Log)**

*AIエージェントは、各タスク完了後にこのリストを更新すること。*

* [x] **Phase 0**
  * [x] Task 0.1, 0.2, 0.3, 0.4
  * [x] Verification 0
* [x] **Phase 1**
  * [x] Task 1.1
  * [x] Verification 1
* [x] **Phase 2**
  * [x] Task 2.1
  * [x] Task 2.2
  * [x] Verification 2
* [x] **Phase 3**
  * [x] Task 3.1
  * [x] Task 3.2
  * [x] Verification 3

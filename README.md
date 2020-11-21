# music-bot

このBotは次の記事を参考に作成したものです。
[Discord Bot 最速チュートリアル【Python&Heroku&GitHub】 - Qiita](https://qiita.com/1ntegrale9/items/aa4b373e8895273875a8)
[discord.pyとGoogle Drive APIを利用して音楽Botを作った（Dockerでテスト→Herokuにデプロイ） - Qiita](https://qiita.com/ysk0832/items/372e5beb80df7f752bb5)
[Pythonで始める録音機能付きDiscord Bot: (4) 音楽ファイルを再生する - Qiita](https://qiita.com/Shirataki2/items/f4ea533d5baf55c4b1d3)

また、このリポジトリを作成するにあたり
[DiscordBotPortalJP/discordpy-startup](https://github.com/w-rhino/discordpy-startup)

をベースに作成しております。

## 各種ファイル情報

### __init__.py
現在空のファイルです。

### __main__.py
起動時に呼び出すことになるファイルです。

### auth.py
Googleドライブの認証を行い、アクセストークンを得るためのファイルです。ローカルで走らせます。

### cogs/music.py
Botに音楽再生機能を持たせるファイルです。

### settings.yaml
Googleドライブの認証に関する設定ファイルです。

### secrets
Googleドライブのアクセストークン等を保存するためのディレクトリです。

### requirements.txt
使用しているPythonのライブラリ情報の設定ファイルです。

### Procfile
Herokuでのプロセス実行コマンドの設定ファイルです。

### runtime.txt
Herokuでの実行環境の設定ファイルです。

### .github/workflows/flake8.yaml
GitHub Actions による自動構文チェックの設定ファイルです。

### .gitignore
Git管理が不要なファイル/ディレクトリの設定ファイルです。

### LICENSE
このリポジトリのコードの権利情報です。MITライセンスの範囲でご自由にご利用ください。

### README.md
このドキュメントです。

## 導入方法

### Googleドライブの認証

このリポジトリをプルしたら、secretsディレクトリ下にOAuth 2.0 クライアント IDのjsonファイルを入れてください。
またこのjsonファイル名をsettings.yamlのclient_config_fileの欄に書き込んでください。

なおGoogle Drive APIに関連する準備は
https://note.nkmk.me/python-pydrive-download-upload-delete/
こちらを参照してください。

次にauth.pyを走らせると認証画面が出てきますので、画面に従い処理を行ってください。認証が完了すると、secretディレクトリ下にconfidentials.jsonが作成されています。
confidentials.jsonにはアクセストークンが入っていますので、外部に公開しないようにしましょう。

### Botの準備・Herokuへデプロイ

[Discord Bot 最速チュートリアル【Python&Heroku&GitHub】 - Qiita](https://qiita.com/1ntegrale9/items/aa4b373e8895273875a8)
に従い進めていき（既にリポジトリがあるため、手順２，３は飛ばして大丈夫です）、デプロイを行ってください。
これでBotが上手く起動するはずです。

### 音楽ファイルを入れる

botは次のファイルを読み込みます。
$play と入力した場合
Googleドライブ内の「music-bot」フォルダ内の音楽を全て再生リストに入れ、シャッフル再生します。
$play hoge と入力した場合
Googleドライブ内の「music-bot」フォルダの中にある「playlist_hoge」フォルダ内の音楽を全て再生リストに入れ、シャッフル再生します。

音楽ファイルを読み込む際にHerokuの一時ファイルとして保存する仕様上、大きすぎる音楽ファイルはBotが落ちる原因となりますのでご注意ください。



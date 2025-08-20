# main.py
# Version: 4.21
# Updated: 2025-06-09 18:50
# ワザ使用システム完全実装版

import tkinter as tk
import os
import sys

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 必要なディレクトリの作成
def ensure_directories():
    """必要なディレクトリが存在することを確認"""
    directories = ["cards", "database", "gui", "models", "utils"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"{directory}ディレクトリを作成しました。")

def check_csv_files():
    """必要なCSVファイルの存在確認"""
    csv_files = ["cards/cards.csv", "cards/deck.csv"]
    missing_files = []
    
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            missing_files.append(csv_file)
    
    if missing_files:
        print("⚠️  以下のCSVファイルが見つかりません:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nデモ用のサンプルファイルを作成することをお勧めします。")
        return False
    
    return True

def main():
    """メインエントリーポイント"""
    print("ポケモンカードゲーム シミュレータ v4.21 起動中...")
    print("🎯 v4.21の新機能: ワザ使用システム完全実装")
    print("")
    print("⚔️ ワザ使用システムの主要機能:")
    print("   ✅ エネルギーコスト判定システム")
    print("      - 必要エネルギーと装着エネルギーの照合")
    print("      - 無色エネルギーの代用計算")
    print("      - 詳細なエラーメッセージ表示")
    print("")
    print("   ✅ 攻撃選択ダイアログ")
    print("      - 使用可能なワザの一覧表示")
    print("      - エネルギー状況の詳細表示")
    print("      - 右クリック攻撃メニュー")
    print("")
    print("   ✅ ダメージ計算・適用システム")
    print("      - 弱点・抵抗力の自動計算")
    print("      - HPダメージの適用")
    print("      - きぜつ判定とサイド獲得")
    print("")
    print("   ✅ AI対戦システム強化")
    print("      - AIの戦略的エネルギー配分")
    print("      - AIの最適ワザ選択")
    print("      - ダメージ効率を考慮した行動")
    print("")
    print("🎮 継承された機能:")
    print("   ✅ エネルギー装着対象選択機能")
    print("   ✅ 進化制限システム（正式ルール準拠）")
    print("   ✅ ターン開始時自動ドロー")
    print("   ✅ マリガン・初期配置システム")
    print("   ✅ UIレイアウト最適化")
    
    # 必要なディレクトリの作成
    ensure_directories()
    
    # CSVファイルの確認
    if not check_csv_files():
        print("必要なデータファイルが不足していますが、デモモードで起動します。")
    
    # Tkinterのルートウィンドウを作成
    root = tk.Tk()
    
    try:
        # データベースマネージャーの初期化
        from database.database_manager import DatabaseManager
        database_manager = DatabaseManager()
        
        # メインGUIの起動
        from gui.main_gui import PokemonTCGGUI
        app = PokemonTCGGUI(root, database_manager)
        
        print("✅ アプリケーション起動成功")
        print("\n⚔️ ワザ使用システムの使い方:")
        print("1. ゲームを開始し、初期配置を完了します")
        print("2. 手札からエネルギーカードを使ってポケモンにエネルギーを装着します")
        print("3. バトル場またはベンチのポケモンを右クリックします")
        print("4. 攻撃メニューが表示されるので、使用したいワザを選択します")
        print("5. エネルギーが足りている場合、ワザ選択ダイアログが表示されます")
        print("6. 「攻撃実行」ボタンでワザを発動し、ダメージを与えます")
        print("7. 攻撃後は自動的にターンが終了します")
        print("")
        print("🎯 戦略のポイント:")
        print("- エネルギーを効率よく配分してワザを使用可能にする")
        print("- 弱点を狙って2倍ダメージを与える")
        print("- 相手のHPを削ってきぜつさせ、サイドを獲得する")
        print("- 6枚のサイドをすべて取ると勝利！")
        print("")
        print("📊 技術的改善:")
        print("- ワザ使用の完全実装")
        print("- エネルギーコスト判定の精密化")
        print("- ダメージ計算の正確性向上")
        print("- AIの戦略的思考の実装")
        print("- ゲーム終了条件の完全実装")
        
        # メインループを開始
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("必要なモジュールが見つかりません。")
        
        # エラー詳細の表示
        print("\n🔍 デバッグ情報:")
        print(f"Python パス: {sys.path}")
        print(f"作業ディレクトリ: {os.getcwd()}")
        print(f"Pythonバージョン: {sys.version}")
        
        # 基本的なファイル構造チェック
        print("\n📁 ファイル構造チェック:")
        for root_dir, dirs, files in os.walk("."):
            level = root_dir.replace(".", "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root_dir)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                if file.endswith(('.py', '.csv')):
                    print(f"{subindent}{file}")
        
        # フォールバック: 簡易エラーダイアログ
        try:
            from tkinter import messagebox
            messagebox.showerror(
                "起動エラー", 
                f"アプリケーションの起動に失敗しました。\n\nエラー: {str(e)}\n\n"
                "必要なファイルが不足している可能性があります。"
            )
        except:
            pass
        
        root.quit()
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        
        # エラーダイアログを表示
        try:
            from tkinter import messagebox
            messagebox.showerror("エラー", f"アプリケーションでエラーが発生しました：\n{str(e)}")
        except:
            pass
        
        root.quit()

if __name__ == "__main__":
    main()
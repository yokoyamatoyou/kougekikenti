import threading
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox

from modules.analyzer import Analyzer
from modules.scraper import Scraper


class ModerationApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("テキストモデレーションツール")
        self.geometry("800x600")

        self.df: pd.DataFrame | None = None
        self.analyzer = Analyzer()
        self.scraper = Scraper()
        self.create_ui()

    def create_ui(self) -> None:
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="テキストモデレーション分析",
            font=("Helvetica", 24, "bold"),
        )
        self.title_label.pack(pady=20)

        self.settings_frame = ctk.CTkFrame(self.main_frame)
        self.settings_frame.pack(pady=10, padx=20, fill="x")

        self.username_entry = ctk.CTkEntry(self.settings_frame, width=120, placeholder_text="XユーザーID")
        self.username_entry.pack(side="left", padx=5)

        self.limit_entry = ctk.CTkEntry(self.settings_frame, width=60, placeholder_text="取得件数")
        self.limit_entry.pack(side="left", padx=5)

        self.temp_entry = ctk.CTkEntry(self.settings_frame, width=60)
        self.temp_entry.pack(side="left", padx=5)
        self.temp_entry.insert(0, str(self.analyzer.temperature))

        self.top_p_entry = ctk.CTkEntry(self.settings_frame, width=60)
        self.top_p_entry.pack(side="left", padx=5)
        self.top_p_entry.insert(0, str(self.analyzer.top_p))

        self.status_label = ctk.CTkLabel(self.main_frame, text="ユーザーIDを入力してください")
        self.status_label.pack(pady=10)

        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(pady=20)

        self.run_button = ctk.CTkButton(
            self.button_frame,
            text="収集＆分析開始",
            command=self.run_analysis,
        )
        self.run_button.pack(pady=10)

        self.save_button = ctk.CTkButton(
            self.button_frame,
            text="結果を保存",
            command=self.save_results,
            state="disabled",
        )
        self.save_button.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

    def run_analysis(self) -> None:
        self.run_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        thread = threading.Thread(target=self._run_analysis_thread, daemon=True)
        thread.start()

    def _run_analysis_thread(self) -> None:
        username = self.username_entry.get().strip()
        limit_str = self.limit_entry.get().strip()
        try:
            limit = int(limit_str) if limit_str else 20
        except ValueError:
            self.after(0, lambda: self.status_label.configure(text="取得件数が不正です", text_color="red"))
            self.after(0, lambda: self.run_button.configure(state="normal"))
            return

        self.after(0, lambda: self.status_label.configure(text="投稿を取得中..."))
        df = self.scraper.scrape_user_posts(username, limit)
        if df.empty:
            self.after(0, lambda: self.status_label.configure(text="投稿が取得できませんでした", text_color="red"))
            self.after(0, lambda: self.run_button.configure(state="normal"))
            return

        self.df = df

        category_names = [
            "hate",
            "hate/threatening",
            "self-harm",
            "sexual",
            "sexual/minors",
            "violence",
            "violence/graphic",
        ]
        category_flags = {name: [] for name in category_names}
        category_scores = {name: [] for name in category_names}
        aggressiveness_scores = []
        aggressiveness_reasons = []

        total_rows = len(self.df)

        for index, row in self.df.iterrows():
            text = row["content"]
            categories, scores = self.analyzer.moderate_text(text)
            for name in category_names:
                category_flags[name].append(getattr(categories, name.replace("/", "_"), False))
                category_scores[name].append(getattr(scores, name.replace("/", "_"), 0.0))
            score, reason = self.analyzer.get_aggressiveness_score(text)
            aggressiveness_scores.append(score)
            aggressiveness_reasons.append(reason)

            progress = (index + 1) / total_rows
            self.after(0, lambda p=progress, i=index + 1: (
                self.progress_bar.set(p),
                self.status_label.configure(text=f"分析中... {i}/{total_rows}"),
            ))

        for name in category_names:
            self.df[f"{name}_flag"] = category_flags[name]
            self.df[f"{name}_score"] = category_scores[name]
        self.df["aggressiveness_score"] = aggressiveness_scores
        self.df["aggressiveness_reason"] = aggressiveness_reasons
        self.df["total_aggression"] = self.df.apply(self.analyzer.total_aggression, axis=1)

        self.after(0, lambda: (
            self.status_label.configure(text="分析が完了しました", text_color="green"),
            self.save_button.configure(state="normal"),
            self.run_button.configure(state="normal"),
        ))

    def save_results(self) -> None:
        save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not save_path:
            return
        try:
            self.df.to_excel(save_path, index=False)
            self.status_label.configure(text="結果を保存しました", text_color="green")
        except Exception as e:
            self.status_label.configure(text="保存に失敗しました", text_color="red")
            messagebox.showerror("保存エラー", f"ファイルを保存できませんでした: {e}")

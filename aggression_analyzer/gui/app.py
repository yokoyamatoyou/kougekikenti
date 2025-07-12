import threading
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox

from modules.analyzer import Analyzer
from modules.scraper import Scraper, archive_url


class ModerationApp(ctk.CTk):
    """Desktop GUI for scraping and analyzing posts."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("テキストモデレーションツール")
        self.geometry("800x600")

        self.df: pd.DataFrame | None = None
        self.analyzer = Analyzer()
        self.scraper = Scraper()
        self.result_items: list[dict[str, object]] = []
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

        self.username_entry = ctk.CTkEntry(
            self.settings_frame,
            width=120,
            placeholder_text="XユーザーID",
        )
        self.username_entry.pack(side="left", padx=5)

        self.limit_entry = ctk.CTkEntry(
            self.settings_frame,
            width=60,
            placeholder_text="取得件数",
        )
        self.limit_entry.pack(side="left", padx=5)

        self.temp_entry = ctk.CTkEntry(self.settings_frame, width=60)
        self.temp_entry.pack(side="left", padx=5)
        self.temp_entry.insert(0, str(self.analyzer.temperature))

        self.top_p_entry = ctk.CTkEntry(self.settings_frame, width=60)
        self.top_p_entry.pack(side="left", padx=5)
        self.top_p_entry.insert(0, str(self.analyzer.top_p))

        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="ユーザーIDを入力してください",
        )
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

        self.threshold_frame = ctk.CTkFrame(self.main_frame)
        self.threshold_frame.pack(pady=5, fill="x")
        self.threshold_slider = ctk.CTkSlider(
            self.threshold_frame,
            from_=0,
            to=10,
            number_of_steps=10,
            command=self.on_threshold_change,
        )
        self.threshold_slider.set(5)
        self.threshold_slider.pack(side="left", padx=5)
        self.threshold_label = ctk.CTkLabel(
            self.threshold_frame, text="自動選択スコア: 5"
        )
        self.threshold_label.pack(side="left", padx=5)

        self.results_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            height=200,
        )
        self.results_frame.pack(fill="both", expand=True, pady=10)

        self.archive_button = ctk.CTkButton(
            self.main_frame,
            text="選択した投稿の魚拓をまとめて作成",
            command=self.batch_archive,
            state="disabled",
        )
        self.archive_button.pack(pady=5)

    def run_analysis(self) -> None:
        self.run_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        thread = threading.Thread(
            target=self._run_analysis_thread,
            daemon=True,
        )
        thread.start()

    def _run_analysis_thread(self) -> None:
        """Collect posts and run the analysis in a background thread."""
        username = self.username_entry.get().strip()
        limit_str = self.limit_entry.get().strip()
        try:
            limit = int(limit_str) if limit_str else 20
        except ValueError:
            self.after(
                0,
                lambda: self.status_label.configure(
                    text="取得件数が不正です", text_color="red"
                ),
            )
            self.after(0, lambda: self.run_button.configure(state="normal"))
            return

        self.after(
            0, lambda: self.status_label.configure(text="投稿を取得中...")
        )
        df = self.scraper.scrape_user_posts(username, limit)
        if df.empty:
            self.after(
                0,
                lambda: self.status_label.configure(
                    text="投稿が取得できませんでした", text_color="red"
                ),
            )
            self.after(0, lambda: self.run_button.configure(state="normal"))
            return

        self.df = df

        total_rows = len(self.df)

        def progress(done: int, total: int = total_rows) -> None:
            p = done / total
            self.after(
                0,
                lambda: (
                    self.progress_bar.set(p),
                    self.status_label.configure(
                        text=f"分析中... {done}/{total}"
                    ),
                ),
            )

        self.df = self.analyzer.analyze_dataframe_in_parallel(
            self.df, progress
        )
        self.after(0, self._display_results)

    def save_results(self) -> None:
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
        )
        if not save_path:
            return
        try:
            self.df.to_excel(save_path, index=False)
            self.status_label.configure(text="結果を保存しました", text_color="green")
        except Exception as e:
            self.status_label.configure(text="保存に失敗しました", text_color="red")
            messagebox.showerror(
                "保存エラー",
                f"ファイルを保存できませんでした: {e}",
            )

    def on_threshold_change(self, value: float) -> None:
        score = int(float(value))
        self.threshold_label.configure(text=f"自動選択スコア: {score}")
        for item in self.result_items:
            idx = item["index"]
            post_score = (
                self.df.loc[idx, "aggressiveness_score"]
                if self.df is not None
                else 0
            )
            item["var"].set(post_score >= score)

    def _display_results(self) -> None:
        if self.df is None:
            return
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.result_items.clear()
        threshold = int(self.threshold_slider.get())
        for idx, row in self.df.iterrows():
            color = "gray20"
            if row["aggressiveness_score"] >= 7:
                color = "#8b0000"
            elif row["aggressiveness_score"] >= 4:
                color = "#555500"
            frame = ctk.CTkFrame(self.results_frame, fg_color=color)
            frame.pack(fill="x", pady=2)
            var = ctk.BooleanVar(
                value=row["aggressiveness_score"] >= threshold
            )
            chk = ctk.CTkCheckBox(frame, variable=var)
            chk.pack(side="left")
            text = f"{row['aggressiveness_score']}: {row['content'][:50]}"
            label = ctk.CTkLabel(frame, text=text, anchor="w")
            label.pack(side="left", padx=5)
            status = ctk.CTkLabel(frame, text="")
            status.pack(side="right", padx=5)
            self.result_items.append({
                "index": idx,
                "var": var,
                "status": status,
            })
        self.save_button.configure(state="normal")
        self.run_button.configure(state="normal")
        self.archive_button.configure(state="normal")
        self.status_label.configure(text="分析が完了しました", text_color="green")

    def batch_archive(self) -> None:
        self.archive_button.configure(state="disabled")
        thread = threading.Thread(
            target=self._batch_archive_thread,
            daemon=True,
        )
        thread.start()

    def _batch_archive_thread(self) -> None:
        if self.df is None:
            return
        selected = [item for item in self.result_items if item["var"].get()]
        for item in selected:
            idx = item["index"]
            url = self.df.loc[idx, "url"]
            self.after(
                0,
                lambda st=item["status"]: st.configure(text="魚拓作成中..."),
            )
            archive = archive_url(url)
            if archive:
                self.df.loc[idx, "archive_url"] = archive
            self.after(0, lambda st=item["status"]: st.configure(text="完了"))
        self.after(0, lambda: self.archive_button.configure(state="normal"))

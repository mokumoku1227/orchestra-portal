import streamlit as st
import pandas as pd
import datetime

# =========================================================
# アプリケーション設定
# =========================================================
st.set_page_config(page_title="オーケストラ 運営ポータル", layout="wide")

# =========================================================
# 0. データベース（セッションステート）の初期化
#    ※本番環境では外部DB（FirebaseやAWS等）に接続する想定ですが、
#      本デモ版ではアプリ内のメモリにデータを保持します。
# =========================================================
if "attendance_records" not in st.session_state:
    st.session_state.attendance_records = []

if "practice_dates" not in st.session_state:
    st.session_state.practice_dates = ["6/14", "6/21", "6/28"]

# 【個人情報保護】GitHub公開デモ用のダミー名簿データ
if "roster" not in st.session_state:
    st.session_state.roster = [
        {"パート": "フルート", "学年": "3年", "名前": "青木"},
        {"パート": "クラリネット", "学年": "2年", "名前": "伊藤"},
        {"パート": "トランペット", "学年": "1年", "名前": "宇野"},
        {"パート": "ホルン", "学年": "3年", "名前": "遠藤"},
        {"パート": "トロンボーン", "学年": "2年", "名前": "岡田"},
        {"パート": "パーカッション", "学年": "1年", "名前": "加藤"}
    ]

# 固定のパート順
part_order = ["フルート", "クラリネット", "トランペット", "ホルン", "トロンボーン", "パーカッション"]

st.title("オーケストラ 運営ポータル（デモ版）")
st.caption("※このアプリはポートフォリオ用のデモ版です。ダミーデータを使用しています。")

# =========================================================
# 1. サイドバー（ユーザー設定 ＆ 認証システム）
# =========================================================
st.sidebar.header("👤 ユーザー設定")
user_part = st.sidebar.selectbox(
    "パートを選択", 
    ["選択してください"] + part_order
)

user_role = st.sidebar.selectbox(
    "役職 / 係を選択", 
    ["一般団員", "パートリーダー", "学生指揮者", "幹部", "印刷・制作係", "会計係"]
)

# 簡易的なロールベースアクセス制御（RBAC）
is_authenticated = False
if user_role in ["パートリーダー", "学生指揮者", "幹部"]:
    password = st.sidebar.text_input(f"🔑 {user_role}のパスワードを入力 (demo: music)", type="password")
    if password == "music":
        st.sidebar.success("🔓 認証に成功しました")
        is_authenticated = True
    elif password != "":
        st.sidebar.error("🔒 パスワードが違います")

# 出欠状況確認タブへのアクセス権限（一般団員 または 認証済みの役員）
has_dashboard_access = (user_role == "一般団員") or is_authenticated

# 日付選択UIの自動計算
view_date = None
if has_dashboard_access and st.session_state.practice_dates:
    st.sidebar.divider()
    st.sidebar.header("📅 閲覧設定")
    
    today = datetime.date.today()
    default_date_idx = 0
    
    for i, date_str in enumerate(st.session_state.practice_dates):
        try:
            month, day = map(int, date_str.split('/'))
            target_dt = datetime.date(today.year, month, day)
            if target_dt >= today:
                default_date_idx = i
                break
        except:
            pass

    view_date = st.sidebar.selectbox(
        "表示する出欠の日付", 
        st.session_state.practice_dates, 
        index=default_date_idx
    )

st.divider()

# =========================================================
# 2. メインビュー（4つのタブ）
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(["📝 出欠登録フォーム", "👥 団員名簿管理", "📋 練習日管理", "📊 出欠状況確認"])

# ---------------------------------------------------------
# 【タブ1】出欠登録フォーム
# ---------------------------------------------------------
with tab1:
    st.subheader("本日の出欠登録")
    
    if user_part != "選択してください":
        st.info(f"👤 あなたは **{user_part}** パートとして操作しています。")
        
        if not st.session_state.practice_dates:
            st.warning("現在、登録可能な練習日がありません。学生指揮者が日程を追加するのをお待ちください。")
        else:
            register_date = st.radio("登録する練習日", st.session_state.practice_dates, horizontal=True)
            st.write("") 
            
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("名前", placeholder="例：音楽 太郎")
            with col2:
                grade = st.selectbox("学年", ["1年", "2年", "3年"])
                
            status = st.radio(f"{register_date} の状況", ["出席", "遅刻", "早退", "欠席"], horizontal=True)
            reason = st.text_input("備考（遅刻・欠席の理由など）")
            
            if st.button("出欠を送信する", use_container_width=True):
                if name == "":
                    st.error("名前を入力してください。")
                else:
                    new_data = {
                        "日付": register_date,
                        "パート": user_part,
                        "学年": grade,
                        "名前": name,
                        "状況": status,
                        "備考": reason
                    }
                    st.session_state.attendance_records.append(new_data)
                    st.success(f"✨ {register_date}分：{grade} {name} さんの出欠データ（{status}）を保存しました！")
    else:
        st.warning("👈 左のサイドバーから自分の「パート」を選択してください。")

# ---------------------------------------------------------
# 【タブ2】団員名簿管理（マスターデータ管理）
# ---------------------------------------------------------
with tab2:
    st.subheader("👥 団員名簿管理")
    
    if user_role in ["パートリーダー", "幹部"] and is_authenticated:
        # 【追加要件】パート未選択時のバリデーション
        if user_role == "パートリーダー" and user_part == "選択してください":
            st.warning("👈 左のサイドバーで自分のパートを選択してから、名簿を編集してください。")
        else:
            if user_role == "幹部":
                st.success("🔓 幹部権限：全パートの名簿を管理・編集できます。")
                edit_part = st.selectbox("名簿を編集・参照するパートを選択", part_order)
            else:
                st.info(f"🔓 パートリーダー権限：あなたのパート（{user_part}）のみ管理できます。")
                edit_part = user_part

            st.divider()

            # --- 新規追加フォーム ---
            with st.form("add_member_form", clear_on_submit=True):
                st.write(f"**➕ 【{edit_part}】パートへの新規追加**")
                col_g, col_n, col_b = st.columns([1, 2, 1])
                with col_g:
                    new_grade = st.selectbox("学年", ["1年", "2年", "3年"])
                with col_n:
                    new_name = st.text_input("名前", placeholder="例：山田 太郎")
                with col_b:
                    st.write("") 
                    submit_btn = st.form_submit_button("団員を追加")

                if submit_btn:
                    if new_name == "":
                        st.error("名前を入力してください。")
                    else:
                        st.session_state.roster.append({
                            "パート": edit_part,
                            "学年": new_grade,
                            "名前": new_name
                        })
                        st.rerun()

            st.write("")
            st.write(f"**📋 【{edit_part}】パートの現在の名簿**")

            # --- 既存名簿リスト ---
            current_members = [m for m in st.session_state.roster if m["パート"] == edit_part]

            if current_members:
                for member in current_members:
                    col_info, col_del = st.columns([4, 1])
                    with col_info:
                        st.write(f"・ {member['学年']} {member['名前']}")
                    with col_del:
                        if st.button("削除", key=f"del_{member['パート']}_{member['名前']}"):
                            st.session_state.roster.remove(member)
                            st.rerun()
            else:
                st.write("現在、このパートに登録されている団員はいません。")

    elif user_role in ["パートリーダー", "幹部"] and not is_authenticated:
        st.error(f"🔒 {user_role}専用画面を開くには、左のサイドバーで正しいパスワードを入力してください。")
    else:
        st.error("🔒 この画面は【パートリーダー】または【幹部】のみ閲覧・編集可能です。")

# ---------------------------------------------------------
# 【タブ3】練習日管理（スケジュールマスタ管理）
# ---------------------------------------------------------
with tab3:
    if user_role == "学生指揮者":
        if is_authenticated:
            st.subheader("📅 練習日の管理")
            col_d1, col_d2 = st.columns([3, 1])
            with col_d1:
                new_date_input = st.date_input("新しい練習日を選択")
            with col_d2:
                st.write("")
                st.write("")
                if st.button("追加する", use_container_width=True):
                    new_date_str = f"{new_date_input.month}/{new_date_input.day}"
                    if new_date_str not in st.session_state.practice_dates:
                        st.session_state.practice_dates.append(new_date_str)
                        def sort_key(d_str):
                            m, d = map(int, d_str.split('/'))
                            return m * 100 + d
                        st.session_state.practice_dates.sort(key=sort_key)
                        st.rerun()
                    else:
                        st.warning("その日付はすでに追加されています。")
            st.divider()
            st.write("**現在の登録済み練習日一覧:**")
            for d in st.session_state.practice_dates:
                col_list1, col_list2 = st.columns([4, 1])
                with col_list1:
                    st.write(f"・ {d}")
                with col_list2:
                    if st.button("削除", key=f"del_date_{d}"):
                        st.session_state.practice_dates.remove(d)
                        st.rerun()
        else:
            st.error("🔒 練習日の管理を行うにはパスワードを入力してください。")
    else:
        st.write("※現在、このタブは【学生指揮者】専用のスケジュール管理機能となっています。")

# ---------------------------------------------------------
# 【タブ4】出欠状況ダッシュボード（データ連携・多重ソート）
# ---------------------------------------------------------
with tab4:
    if has_dashboard_access and view_date:
        st.subheader(f"📊 {view_date} の団員出欠状況一覧")
        
        if st.session_state.attendance_records:
            all_df = pd.DataFrame(st.session_state.attendance_records)
            df = all_df[all_df["日付"] == view_date]
            
            if not df.empty:
                # ソート順の定義
                status_order = ["出席", "遅刻", "早退", "欠席"]
                grade_order = ["1年", "2年", "3年"]
                
                df["状況"] = pd.Categorical(df["状況"], categories=status_order, ordered=True)
                df["学年"] = pd.Categorical(df["学年"], categories=grade_order, ordered=True)
                
                # スタイリング関数
                def highlight_rows(row):
                    status = row["状況"]
                    if status == "出席": return ["background-color: rgba(144, 238, 144, 0.2)"] * len(row)
                    elif status == "遅刻": return ["background-color: rgba(173, 216, 230, 0.3)"] * len(row)
                    elif status == "早退": return ["background-color: rgba(255, 255, 224, 0.6)"] * len(row)
                    elif status == "欠席": return ["background-color: rgba(255, 182, 193, 0.3)"] * len(row)
                    return [""] * len(row)

                # 出席者サマリー生成関数（名簿DBと連携）
                def display_summary_table(target_df):
                    st.markdown("#### 📈 パート別 出席者サマリー")
                    summary_dict = {}
                    for p in part_order:
                        attend_count = len(target_df[(target_df["パート"] == p) & (target_df["状況"] == "出席")])
                        total = len([m for m in st.session_state.roster if m["パート"] == p])
                        summary_dict[p] = f"{attend_count}人 ({total}人中)"
                    
                    summary_df = pd.DataFrame([summary_dict])
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    st.divider()

                # ==========================================
                # 【A】幹部 ＆ 学生指揮者のビュー
                # ==========================================
                if user_role in ["幹部", "学生指揮者"]:
                    st.success(f"🔓 {user_role}権限：全パートの出欠状況を一覧表示しています。")
                    display_summary_table(df)
                    
                    for p in part_order:
                        group_data = df[df["パート"] == p]
                        if not group_data.empty:
                            st.markdown(f"**■ {p}**")
                            sorted_group_df = group_data.sort_values(["状況", "学年"])
                            styled_group_df = sorted_group_df.drop(columns=["日付", "パート"]).style.apply(highlight_rows, axis=1)
                            st.dataframe(styled_group_df, use_container_width=True, hide_index=True)

                # ==========================================
                # 【B】パートリーダーのビュー
                # ==========================================
                elif user_role == "パートリーダー":
                    st.info(f"🔓 パートリーダー権限：現在選択中の【{user_part}】パートの状況を最優先で表示しています。")
                    
                    st.markdown(f"### 👑 あなたのパート ({user_part})")
                    my_part_df = df[df["パート"] == user_part].sort_values(["状況", "学年"])
                    if not my_part_df.empty:
                        display_df = my_part_df.drop(columns=["日付", "パート"])
                        styled_df = display_df.style.apply(highlight_rows, axis=1)
                        st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    else:
                        st.write("この日付のあなたのパートの登録データはありません。")
                    
                    st.divider()
                    display_summary_table(df)
                    
                    st.markdown("### 🎺 その他のパート")
                    other_parts_df = df[df["パート"] != user_part]
                    if not other_parts_df.empty:
                        for p in part_order:
                            if p == user_part: continue
                            group_data = other_parts_df[other_parts_df["パート"] == p]
                            if not group_data.empty:
                                st.markdown(f"**■ {p}**")
                                sorted_group_df = group_data.sort_values(["状況", "学年"])
                                styled_group_df = sorted_group_df.drop(columns=["日付", "パート"]).style.apply(highlight_rows, axis=1)
                                st.dataframe(styled_group_df, use_container_width=True, hide_index=True)
                    else:
                        st.write("この日付のその他のパートの登録データはありません。")

                # ==========================================
                # 【C】一般団員のビュー
                # ==========================================
                elif user_role == "一般団員":
                    st.info("🔒 一般団員権限：あなた自身のパートの出欠状況と、全体のサマリーのみ閲覧できます。")
                    
                    st.markdown(f"### 🎺 あなたのパート ({user_part})")
                    my_part_df = df[df["パート"] == user_part].sort_values(["状況", "学年"])
                    if not my_part_df.empty:
                        display_df = my_part_df.drop(columns=["日付", "パート"])
                        styled_df = display_df.style.apply(highlight_rows, axis=1)
                        st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    else:
                        st.write("この日付のあなたのパートの登録データはありません。")
                        
                    st.divider()
                    display_summary_table(df)

            else:
                st.write(f"まだ {view_date} の出欠登録データはありません。")
                
        else:
            st.write("現在、送信された出欠データはありません。")
            
    elif user_role in ["パートリーダー", "学生指揮者", "幹部"] and not is_authenticated:
        st.error(f"🔒 {user_role}専用画面を開くには、左のサイドバーで正しいパスワードを入力してください。")
    else:
        if user_part == "選択してください":
            st.warning("👈 左のサイドバーで「パート」を選択してください。")
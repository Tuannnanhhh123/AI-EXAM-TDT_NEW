# ============================================================
# ui.py — CSS styles & các component dùng chung
# ============================================================
import streamlit as st
from config import GRADE_CONFIG, GROQ_MODEL

# ── CSS ──────────────────────────────────────────────────
CSS = """
<style>
    .main-title  { font-size:2.4rem; font-weight:800; color:#1a73e8; text-align:center; }
    .sub-title   { font-size:1rem; color:#555; text-align:center; margin-bottom:1rem; }
    .q-box       { background:#f0f4ff; border-left:4px solid #1a73e8;
                   border-radius:8px; padding:1rem 1.2rem; margin-bottom:.8rem; }
    .correct     { color:#1e8e3e; font-weight:600; }
    .wrong       { color:#d93025; font-weight:600; }
    .explain-box { background:#e8f5e9; border-radius:6px; padding:.6rem 1rem;
                   font-size:.88rem; color:#2e7d32; margin-top:.4rem; }
    .timer-box   { font-size:1.3rem; font-weight:700; text-align:center;
                   padding:.5rem; border-radius:8px; }
    .stButton > button { width:100%; border-radius:8px; font-weight:600; padding:.5rem 1rem; }
    .source-badge{ font-size:.72rem; padding:.2rem .6rem; border-radius:99px;
                   font-weight:600; display:inline-block; margin-bottom:.4rem; }
    .badge-ai    { background:#e8f0fe; color:#1a73e8; }
    .badge-local { background:#fce8e6; color:#d93025; }
    .level-tag   { display:inline-block; padding:.15rem .5rem; border-radius:4px;
                   font-size:.75rem; font-weight:700; margin-left:.4rem; }
    .tag-primary { background:#e8f0fe; color:#1565c0; }
    .tag-middle  { background:#e8f5e9; color:#2e7d32; }
    .tag-high    { background:#fff3e0; color:#e65100; }
    .tag-uni     { background:#fce4ec; color:#880e4f; }
</style>
"""

def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("### 🎓 AI Exam Generator")
        st.markdown("---")
        st.markdown("**🤖 AI Engine:**")
        st.code(f"Groq: {GROQ_MODEL}", language=None)
        st.markdown("---")

        # ── Thống kê lịch sử ──────────────────────────
        from history_manager import get_history_stats, clear_history
        stats = get_history_stats()
        if stats:
            st.markdown("**📊 Câu hỏi đã dùng:**")
            for key, count in stats.items():
                subj, grade = key.split("|")
                st.caption(f"• {subj} / {grade.split('(')[0].strip()}: {count} câu")
            if st.button("🗑️ Xóa toàn bộ lịch sử", use_container_width=True):
                clear_history()
                st.success("Đã xóa lịch sử!")
                st.rerun()
        st.markdown("---")

        st.markdown("**📊 Phân loại cấp học:**")
        for lvl, tag in [
            ("Tiểu học","tag-primary"), ("THCS","tag-middle"),
            ("THPT","tag-high"),        ("Đại học","tag-uni"),
        ]:
            grades = [g for g, c in GRADE_CONFIG.items() if c["level"] == lvl]
            label  = ", ".join(g.split("(")[0].strip() for g in grades)
            st.markdown(
                f'<span class="level-tag {tag}">{lvl}</span> {label}',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("""
**Hướng dẫn:**
1. Nhấn **Bắt đầu làm bài**
2. Chọn **Môn học** & **Lớp**
3. Nhấn **Tạo đề thi**
4. Làm bài & **Nộp bài**
        """)

        # Thanh tiến độ khi đang làm bài
        if st.session_state.get("page") == "exam" and st.session_state.get("questions"):
            answered = sum(1 for v in st.session_state.answers.values() if v is not None)
            total    = len(st.session_state.questions)
            st.markdown("---")
            st.progress(answered / total if total > 0 else 0)
            st.caption(f"Tiến độ: {answered}/{total} câu")

        st.markdown("---")
        st.caption("v7.0 · Groq AI · Llama-3.1-8B")
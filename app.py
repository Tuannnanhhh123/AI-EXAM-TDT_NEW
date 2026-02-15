# ============================================================
# app.py — Entry point  |  streamlit run app.py
# ============================================================
import time
import streamlit as st

from ui            import inject_css, render_sidebar
from pages         import show_home, show_select, show_exam, show_results, show_history
from teacher_pages import show_teacher_dashboard

st.set_page_config(page_title="AI Exam Generator", page_icon="🎓", layout="centered")
inject_css()

# ── Session state defaults ────────────────────────────────
_DEFAULTS = {
    "page":               "login",
    "username":           None,
    "uid":                None,
    "email":              None,
    "role":               None,
    "grade":              None,
    "favorite_subjects":  [],
    "subject":            None,
    "questions":          [],
    "answers":            {},
    "submitted":          False,
    "score":              0,
    "start_time":         None,
    "exam_source":        None,
    "ai_error":           None,
    "verify_summary":     None,
    "dup_filtered":       0,
    "exam_start_ts":      None,
    "current_assignment": None,
    "remind_assignments": [],
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Router học sinh ───────────────────────────────────────
_ROUTER = {
    "home":    show_home,
    "select":  show_select,
    "exam":    show_exam,
    "result":  show_results,
    "history": show_history,
}


# ─────────────────────────────────────────────────────────
# TRANG LÀM ĐỀ BẮT BUỘC
# ─────────────────────────────────────────────────────────
def _show_urgent_exam():
    from ai_engine       import generate_exam
    from teacher_manager import get_exam_questions, get_teacher_exams

    a = st.session_state.get("current_assignment")
    if not a:
        st.session_state.page = "home"; st.rerun(); return

    if st.session_state.page in ("exam", "result"):
        render_sidebar()
        _ROUTER[st.session_state.page](); return

    dl_str = f"<br>⏰ Hạn nộp: <b>{a['deadline']}</b>" if a.get("deadline") else ""
    st.markdown(
        f'<div style="background:#fce8e6;border-left:5px solid #d93025;'
        f'padding:1rem 1.2rem;border-radius:8px;margin-bottom:1.5rem">'
        f'🔴 <b>Đề bắt buộc từ giáo viên</b><br>'
        f'📌 {a["title"]}<br>📚 {a["subject"]} — {a["grade"]}{dl_str}</div>',
        unsafe_allow_html=True)

    if st.button("▶ Bắt đầu làm bài ngay", type="primary", use_container_width=True):
        if a.get("exam_id"):
            exam_info = next((e for e in get_teacher_exams() if e["id"]==a["exam_id"]), None)
            qs     = get_exam_questions(exam_info["q_ids"]) if exam_info else []
            source = "local"
        else:
            qs, source = generate_exam(a["subject"], a["grade"])
        if not qs:
            st.error("Không lấy được câu hỏi. Vui lòng thử lại!"); return
        now = time.time()
        st.session_state.update({
            "subject": a["subject"], "grade": a["grade"],
            "questions": qs, "answers": {}, "submitted": False,
            "score": 0, "start_time": now, "exam_start_ts": now,
            "exam_source": source, "page": "exam",
        })
        st.rerun()


# ─────────────────────────────────────────────────────────
# MÀN HÌNH LOGIN / ĐĂNG KÝ
# ─────────────────────────────────────────────────────────
if st.session_state.page == "login":
    from firebase_manager import login, register, reset_password, is_firebase_ok
    from config           import TEACHER_CODE, GRADE_CONFIG, SUBJECT_OPTIONS

    st.markdown('<div class="main-title">🎓 AI Exam Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Hệ thống ôn thi thông minh</div>',
                unsafe_allow_html=True)
    st.markdown("---")

    if not is_firebase_ok():
        st.warning("⚠️ Firebase chưa kết nối — kiểm tra file cấu hình.", icon="🔥")

    # ── Chọn vai trò ─────────────────────────────────────
    role_choice = st.radio("👤 Bạn là:", ["🎒 Học sinh", "👩‍🏫 Giáo viên"],
                           horizontal=True)
    is_teacher  = (role_choice == "👩‍🏫 Giáo viên")
    st.markdown("---")

    if is_teacher:
        # ── Đăng nhập giáo viên (teacher code) ──────────
        st.markdown("### 👩‍🏫 Đăng nhập Giáo viên")
        name = st.text_input("Tên giáo viên", placeholder="VD: Nguyễn Thị B")
        code = st.text_input("🔑 Mã giáo viên", type="password")
        if st.button("🔓 Đăng nhập", type="primary", use_container_width=True):
            if not name.strip():
                st.error("Vui lòng nhập tên!")
            elif code != TEACHER_CODE:
                st.error("❌ Mã giáo viên không đúng!")
            else:
                st.session_state.update({
                    "username": name.strip(), "role": "teacher", "page": "teacher"
                })
                st.rerun()

    else:
        # ── Tab Đăng nhập / Đăng ký học sinh ────────────
        tab_login, tab_register, tab_reset = st.tabs(
            ["🔑 Đăng nhập", "📝 Đăng ký", "🔒 Quên mật khẩu"]
        )

        # ── Đăng nhập ────────────────────────────────────
        with tab_login:
            st.markdown("### 🔑 Đăng nhập")
            email_l = st.text_input("📧 Email", key="l_email",
                                     placeholder="email@example.com")
            pass_l  = st.text_input("🔒 Mật khẩu", type="password", key="l_pass")
            if st.button("▶ Đăng nhập", type="primary",
                         use_container_width=True, key="btn_login"):
                if not email_l or not pass_l:
                    st.error("Vui lòng nhập đầy đủ!")
                else:
                    with st.spinner("Đang đăng nhập..."):
                        ok, msg, user = login(email_l.strip(), pass_l)
                    if ok:
                        from user_manager import create_user
                        create_user(user["display_name"])
                        st.session_state.update({
                            "uid":               user["uid"],
                            "email":             user["email"],
                            "username":          user["display_name"],
                            "role":              "student",
                            "grade":             user.get("grade", ""),
                            "favorite_subjects": user.get("favorite_subjects", []),
                            "page":              "home",
                        })
                        st.success(msg); st.rerun()
                    else:
                        st.error(msg)

        # ── Đăng ký ──────────────────────────────────────
        with tab_register:
            st.markdown("### 📝 Tạo tài khoản mới")
            r_name  = st.text_input("👤 Họ và tên",  key="r_name",
                                     placeholder="VD: Nguyễn Văn A")
            r_email = st.text_input("📧 Email",       key="r_email",
                                     placeholder="email@example.com")
            r_pass  = st.text_input("🔒 Mật khẩu (≥6 ký tự)", type="password",
                                     key="r_pass")
            r_pass2 = st.text_input("🔒 Xác nhận mật khẩu",   type="password",
                                     key="r_pass2")

            c1, c2  = st.columns(2)
            with c1:
                r_grade = st.selectbox("🏫 Lớp của bạn",
                                        list(GRADE_CONFIG.keys()), key="r_grade")
            with c2:
                # Chỉ hiện môn phù hợp với lớp
                avail_subs = GRADE_CONFIG[r_grade]["subjects"]
                r_subjects = st.multiselect("📚 Môn yêu thích",
                                             avail_subs, key="r_subjects")

            if st.button("✅ Tạo tài khoản", type="primary",
                         use_container_width=True, key="btn_register"):
                errs = []
                if not r_name.strip():       errs.append("Chưa nhập họ tên")
                if not r_email.strip():      errs.append("Chưa nhập email")
                if len(r_pass) < 6:          errs.append("Mật khẩu tối thiểu 6 ký tự")
                if r_pass != r_pass2:        errs.append("Mật khẩu xác nhận không khớp")
                if not r_subjects:           errs.append("Chọn ít nhất 1 môn yêu thích")
                if errs:
                    for e in errs: st.error(e)
                else:
                    with st.spinner("Đang tạo tài khoản..."):
                        ok, msg = register(
                            email=r_email.strip(), password=r_pass,
                            display_name=r_name.strip(),
                            grade=r_grade, favorite_subjects=r_subjects
                        )
                    if ok:
                        st.success(f"🎉 {msg} Vui lòng đăng nhập!")
                    else:
                        st.error(msg)

        # ── Quên mật khẩu ────────────────────────────────
        with tab_reset:
            st.markdown("### 🔒 Đặt lại mật khẩu")
            rst_email = st.text_input("📧 Email đã đăng ký", key="rst_email")
            if st.button("📨 Gửi email đặt lại", use_container_width=True,
                         key="btn_reset"):
                if not rst_email.strip():
                    st.error("Vui lòng nhập email!")
                else:
                    ok, msg = reset_password(rst_email.strip())
                    if ok: st.success(msg)
                    else:  st.error(msg)

    st.stop()


# ─────────────────────────────────────────────────────────
# DASHBOARD GIÁO VIÊN
# ─────────────────────────────────────────────────────────
if st.session_state.role == "teacher":
    with st.sidebar:
        st.markdown("### 👩‍🏫 Giáo viên")
        st.markdown(f"**{st.session_state.username}**")
        st.markdown("---")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            for k, v in _DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()
    show_teacher_dashboard()
    st.stop()


# ─────────────────────────────────────────────────────────
# HỌC SINH — Kiểm tra đề gấp
# ─────────────────────────────────────────────────────────
if st.session_state.role == "student":
    from assignment_manager import get_pending_assignments
    pending  = get_pending_assignments(st.session_state.username)
    required = [a for a in pending if a["is_required"]]
    remind   = [a for a in pending if not a["is_required"]]
    st.session_state["remind_assignments"] = remind

    if required and st.session_state.page not in ("exam", "result", "urgent_exam"):
        st.session_state["current_assignment"] = required[0]
        st.session_state.page = "urgent_exam"
        st.rerun()

if st.session_state.page == "urgent_exam":
    _show_urgent_exam(); st.stop()

# ── Sidebar + Router ──────────────────────────────────────
render_sidebar()
_ROUTER.get(st.session_state.page, show_home)()